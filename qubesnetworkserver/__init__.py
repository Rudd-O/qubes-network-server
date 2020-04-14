import qubes.ext
import qubes.vm.templatevm


class QubesNetworkServerExtension(qubes.ext.Extension):

    def shutdown_routing_for_vm(self, netvm, appvm):
        self.reload_routing_for_vm(netvm, appvm, True)

    def reload_routing_for_vm(self, netvm, appvm, shutdown=False):
        '''Reload the routing method for the VM.'''
        if not netvm.is_running():
            return
        for addr_family in (4, 6):
            ip = appvm.ip6 if addr_family == 6 else appvm.ip
            if ip is None:
                continue
            # report routing method
            self.setup_forwarding_for_vm(netvm, appvm, ip, remove=shutdown)

    def setup_forwarding_for_vm(self, netvm, appvm, ip, remove=False):
        '''
        Record in Qubes DB that the passed VM may be meant to have traffic
        forwarded to and from it, rather than masqueraded from it and blocked
        to it.

        The relevant incantation on the command line to assign the forwarding
        behavior is `qvm-features <VM> routing-method forward`.  If the feature
        is set on the TemplateVM upon which the VM is based, then that counts
        as the forwarding method for the VM as well.

        The counterpart code in qubes-firewall handles setting up the NetVM
        with the proper networking configuration to permit forwarding without
        masquerading behavior.

        If `remove` is True, then we remove the respective routing method from
        the Qubes DB instead.
        '''
        if ip is None:
            return
        routing_method = appvm.features.check_with_template(
            'routing-method', 'masquerade'
        )
        base_file = '/qubes-routing-method/{}'.format(ip)
        if remove:
            netvm.untrusted_qdb.rm(base_file)
        elif routing_method == 'forward':
            netvm.untrusted_qdb.write(base_file, 'forward')
        else:
            netvm.untrusted_qdb.write(base_file, 'masquerade')

    @qubes.ext.handler(
        'domain-feature-set:routing-method',
        'domain-feature-delete:routing-method',
    )
    def on_routing_method_changed(
            self,
            vm,
            ignored_feature,
            **kwargs
    ):
        # pylint: disable=no-self-use,unused-argument
        if 'oldvalue' not in kwargs or kwargs.get('oldvalue') != kwargs.get('value'):
            if vm.netvm:
                self.reload_routing_for_vm(vm.netvm, vm)

    @qubes.ext.handler('domain-qdb-create')
    def on_domain_qdb_create(self, vm, event, **kwargs):
        ''' Fills the QubesDB with firewall entries. '''
        # pylint: disable=unused-argument
        if vm.netvm:
            self.reload_routing_for_vm(vm.netvm, vm)

    @qubes.ext.handler('domain-start')
    def on_domain_started(self, vm, event, **kwargs):
        # pylint: disable=unused-argument
        try:
            for downstream_vm in vm.connected_vms:
                self.reload_routing_for_vm(vm, downstream_vm)
        except AttributeError:
            pass

    @qubes.ext.handler('domain-shutdown')
    def on_domain_shutdown(self, vm, event, **kwargs):
       # pylint: disable=unused-argument
        try:
            for downstream_vm in self.connected_vms:
                self.shutdown_routing_for_vm(vm, downstream_vm)
        except AttributeError:
            pass
        if vm.netvm:
            self.shutdown_routing_for_vm(vm.netvm, vm)
 
    @qubes.ext.handler('net-domain-connect')
    def on_net_domain_connect(self, vm, event):
        # pylint: disable=unused-argument
        if vm.netvm:
            self.reload_routing_for_vm(vm.netvm, vm)

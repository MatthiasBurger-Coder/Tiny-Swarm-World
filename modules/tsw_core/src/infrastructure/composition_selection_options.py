"""Pure request arguments and route projections for one selected policy snapshot."""


def profile_options(operation):
    return {} if operation is None else {'profile_operation': operation}


def platform_request_options(selection, provider, ui, trace, operation):
    options = {**selection, **profile_options(operation)}
    if provider is not None:
        options['node_provider_request'] = provider
    if ui is not None or trace is not None:
        options.update(ui=ui, trace_correlation_id=trace)
    return options


def deployment_request_options(selection, ui, progress, operation):
    options = {**selection, **profile_options(operation)}
    if ui is not None:
        options['ui'] = ui
    if progress is not None:
        options['progress'] = progress
    return options


def project_port_registry(port_registry, resolved, exposure, *, contracts, profile, registry):
    if resolved is None and exposure is None:
        return port_registry
    selected_ids = {port for contract in contracts(profile, resolved, service_exposure=exposure)
                    for port in contract.port_ids}
    return registry(ranges=port_registry.ranges,
        mappings=tuple(mapping for mapping in port_registry.mappings if mapping.port_id in selected_ids),
        metadata=port_registry.metadata)


def forwarding_plans(service_profile, resolved, exposure, *, manifest, plan, strategy):
    return tuple(plan(strategy=strategy, service=requirement.service, listen_port=requirement.port,
        target_port=requirement.port, remediation=('Start WSL socat forwarding after live consent.',))
        for requirement in manifest(service_profile=service_profile, resolved_services=resolved,
                                    service_exposure=exposure).required_ports)

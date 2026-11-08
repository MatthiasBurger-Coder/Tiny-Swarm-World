"""Prepared-Git staging and protected configuration; never reset operator code."""
from pathlib import Path

from tiny_swarm_world.application.ports.lifecycle import LifecycleStateError
from tiny_swarm_world.infrastructure.process.runner import ProcessRunnerError


class PreparedProductInstallation:
    def __init__(self, root, manifests, catalog, source, runner, *, adoption_file=None):
        self.root = Path(root).resolve()
        self.manifests = manifests
        self.catalog = catalog
        self.source = source
        self.runner = runner
        self.adoption_file = adoption_file
        self.state = self.root / '.tiny-swarm-world' / 'product'

    def _command(self, args, *, cwd=None, timeout=30, env=None, input=None):
        try:
            result = self.runner.run_text(args, cwd=cwd or self.root, timeout=timeout, env=env, input=input)
            if result.returncode:
                raise ValueError
            return result.stdout.strip()
        except (ProcessRunnerError, OSError, ValueError):
            raise LifecycleStateError('Product operation failed; preserve checkpoint and staged files, then inspect --recover --preview.') from None

    def plan(self, target):
        from tiny_swarm_world.infrastructure.adapters.lifecycle.product_admission import plan

        return plan(self, target)

    def _source_identity(self):
        from tiny_swarm_world.infrastructure.adapters.lifecycle.product_admission import _source_identity

        return _source_identity(self)

    def _clean_source(self):
        from tiny_swarm_world.infrastructure.adapters.lifecycle.product_admission import _clean_source

        return _clean_source(self)

    def validate(self, plan):
        from tiny_swarm_world.infrastructure.adapters.lifecycle.product_admission import validate

        return validate(self, plan)

    def _host_and_resources(self, plan):
        from tiny_swarm_world.infrastructure.adapters.lifecycle.product_admission import _host_and_resources

        return _host_and_resources(self, plan)

    def directory(self, plan):
        return self.state / 'releases' / plan.target.product.revision

    def bind_configuration(self, plan):
        from tiny_swarm_world.infrastructure.adapters.lifecycle.product_configuration_source import bind

        bind(self, plan)

    def migrate(self, plan):
        from tiny_swarm_world.infrastructure.adapters.lifecycle.product_migration import migrate_product_infra

        migrate_product_infra(self, plan)

    def stage(self, plan):
        from tiny_swarm_world.infrastructure.adapters.lifecycle.product_environment import stage

        stage(self, plan)

    def _verify_checkout(self, plan):
        from tiny_swarm_world.infrastructure.adapters.lifecycle.product_environment import _verify_checkout

        _verify_checkout(self, plan)

    def verify_product(self, plan):
        from tiny_swarm_world.infrastructure.adapters.lifecycle.product_environment import verify_product

        verify_product(self, plan)

    def activate(self, plan):
        from tiny_swarm_world.infrastructure.adapters.lifecycle.product_environment import activate

        activate(self, plan)

    def verify_active(self, plan):
        from tiny_swarm_world.infrastructure.adapters.lifecycle.product_environment import verify_active

        verify_active(self, plan)

    def verify_target_runtime(self, plan):
        from tiny_swarm_world.infrastructure.adapters.lifecycle.product_verification import verify_target_runtime

        verify_target_runtime(self, plan)

    def verify_bound_runtime(self, plan, manifest):
        from tiny_swarm_world.infrastructure.adapters.lifecycle.product_verification import verify_bound_runtime

        return verify_bound_runtime(self, plan, manifest)

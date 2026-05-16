class WorkflowError(Exception):
    pass


class RegistryError(WorkflowError):
    pass


class ConfigError(WorkflowError):
    pass


class SecretError(WorkflowError):
    pass


class ProviderError(WorkflowError):
    pass


class StepError(WorkflowError):
    pass


class BudgetError(WorkflowError):
    pass


class SafetyError(WorkflowError):
    pass

"""Commands on an injected, already authenticated E2B sandbox. MIT.

Connect owns sandbox creation, lifetime, credentials and effect idempotency.
"""

from pydantic import BaseModel, ConfigDict, Field

from zeo_integrations._http import IntegrationError
from zeo_integrations._http.runtime import _bounded


class Command(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    command: str = Field(min_length=1, max_length=65536)
    timeout: int = Field(default=30, ge=1, le=300)


class Client:
    def __init__(self, sandbox):
        self.sandbox = sandbox

    def run(self, command: Command, *, allow_effect: bool = False):
        if allow_effect is not True:
            raise IntegrationError("EFFECT_ADMISSION_REQUIRED")
        command = Command.model_validate(command.model_dump())
        failed = False
        try:
            response = self.sandbox.commands.run(
                command.command, background=False, timeout=command.timeout
            )
            result = {
                "stdout": response.stdout,
                "stderr": response.stderr,
                "exit_code": response.exit_code,
            }
            _bounded(result, 1048576)
        except Exception:
            failed = True
        if failed:
            raise IntegrationError("COMMAND_UNCONFIRMED", outcome_unknown=True)
        return result


class Code(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    code: str = Field(min_length=1, max_length=65536)
    language: str = Field(
        default="python", pattern=r"^(python|javascript|typescript|r|java|bash)$"
    )
    timeout: int = Field(default=30, ge=1, le=300)


class CodeClient:
    """Code in one already bound sandbox, returning data rather than executable UI.

    Rich HTML/JavaScript/SVG display representations are never returned here.
    Sandbox provisioning, lifecycle and durable files remain with its host.
    """

    def __init__(self, sandbox):
        self.sandbox = sandbox

    def run_code(self, query: Code, *, allow_effect: bool = False):
        query = Code.model_validate(query.model_dump())
        if allow_effect is not True:
            raise IntegrationError("EFFECT_ADMISSION_REQUIRED")
        failed = False
        try:
            execution = self.sandbox.run_code(
                query.code, language=query.language, timeout=query.timeout
            )
            result = {
                "stdout": execution.logs.stdout,
                "stderr": execution.logs.stderr,
                "execution_failed": execution.error is not None,
                "text_results": [
                    item.text for item in execution.results if item.text is not None
                ],
            }
            _bounded(result, 1048576)
        except Exception:
            failed = True
        if failed:
            raise IntegrationError("CODE_UNCONFIRMED", outcome_unknown=True)
        return result

from pathlib import Path

from pydantic import ConfigDict, Field

from utils.core import BaseConfig


class FishingConfig(BaseConfig):
    boost: bool = False
    boost_amount: int = Field(default=0, serialization_alias="boost amount")

    model_config = ConfigDict(serialize_by_alias=True)

    def __init__(self, confPath: Path, **data):
        super().__init__(confPath=confPath, **data)

    def _validate_config(self):
        self._assert_populated(self.baits)

    def loadConfig(self, confPath: Path):
        fromYaml = self._loadYamlDict(confPath)

        for confkey, confvalue in fromYaml.items():
            match confkey:
                case "boost":
                    if confvalue and isinstance(confvalue, bool):
                        self.boost = confvalue
                case "boost amount":
                    if confvalue and isinstance(confvalue, int):
                        self.boost_amount = confvalue

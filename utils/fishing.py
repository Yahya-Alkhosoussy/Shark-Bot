from pathlib import Path

from pydantic import ConfigDict, Field

from SQL.sharkGamesSQL import sharkGameSQL as sg
from utils.core import BaseConfig


class FishingConfig(BaseConfig):
    boost: bool = False
    boost_amount: int = Field(default=0, serialization_alias="boost amount")

    model_config = ConfigDict(serialize_by_alias=True)

    def __init__(self, confPath: Path, **data):
        super().__init__(confPath=confPath, **data)

    def _validate_config(self):
        pass

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


def remove_net_use(net: str, user: str) -> tuple[str | None, int]:
    """
    Removed a net use as well as sends the user a warning.

    :param net: This is the net that the user has used
    :type net: str
    :param user: This is the user that has used the net
    :type user: str

    :return str | None: A warning message if the net is about to break or has broken, otherwise returns None
    """

    available_nets, about_to_break, broken_nets, net_uses = sg.get_net_availability(user)
    if net in available_nets:
        if net in about_to_break and net_uses == 21:
            return (
                f"WARNING {user}: Net is about to break, 1 more use left. Do not worry through because you have 4 more of the same net left",  # noqa: E501
                net_uses,
            )
        elif net in about_to_break and net_uses == 16:
            return (
                f"WARNING @{user}: Net is about to break, 1 more use left. Do not worry through because you have 3 more of the same net left",  # noqa: E501
                net_uses,
            )
        elif net in about_to_break and net_uses == 11:
            return (
                f"WARNING @{user}: Net is about to break, 1 more use left. Do not worry through because you have 2 more of the same net left",  # noqa: E501
                net_uses,
            )
        elif net in about_to_break and net_uses == 6:
            return (
                f"WARNING @{user}: Net is about to break, 1 more use left. Do not worry through because you have 1 more of the same net left",  # noqa: E501
                net_uses,
            )
        elif net in about_to_break and net_uses == 1:
            return f"WARNING @{user}: Net is about to break, 1 more use left. This is your last net", net_uses
        if net in broken_nets and net_uses == 20:
            return f"WARNING @{user}: Net broken, don't worry through because you have 4 more of the same net left", net_uses
        elif net in broken_nets and net_uses == 15:
            return f"WARNING @{user}: Net broken, don't worry through because you have 3 more of the same net left", net_uses
        elif net in broken_nets and net_uses == 10:
            return f"WARNING @{user}: Net broken, don't worry through because you have 2 more of the same net left", net_uses
        elif net in broken_nets and net_uses == 5:
            return f"WARNING @{user}: Net broken, don't worry through because you have 1 more of the same net left", net_uses
        elif net in broken_nets and net_uses == 0:
            return f"WARNING @{user}: Net broken. You have no more uses of the same net left", net_uses
    return None, net_uses

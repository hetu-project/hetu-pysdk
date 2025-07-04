from dataclasses import dataclass

from hetu.chain_data.info_base import InfoBase
from hetu.chain_data.utils import decode_account_id


@dataclass
class ProposalVoteData(InfoBase):
    """
    Senate / Proposal data
    """

    index: int
    threshold: int
    ayes: list[str]
    nays: list[str]
    end: int

    @classmethod
    def from_dict(cls, proposal_dict: dict) -> "ProposalVoteData":
        return cls(
            ayes=[decode_account_id(key) for key in proposal_dict["ayes"]],
            end=proposal_dict["end"],
            index=proposal_dict["index"],
            nays=[decode_account_id(key) for key in proposal_dict["nays"]],
            threshold=proposal_dict["threshold"],
        )

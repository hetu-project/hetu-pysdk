from dataclasses import dataclass
from typing import Optional

from hetu.chain_data.info_base import InfoBase
from hetu.utils.balance import Balance


@dataclass
class EVMSubnetInfo(InfoBase):
    """
    Dataclass for EVM subnet information that matches the contract's SubnetInfo structure.
    
    This structure corresponds to the SubnetTypes.SubnetInfo struct in the SubnetManager contract.
    """
    
    # Basic subnet information
    netuid: int
    owner: str  # Owner address
    alpha_token: str  # Alpha token contract address
    amm_pool: str  # AMM pool contract address
    
    # Financial information
    locked_amount: Balance  # Amount locked in the subnet
    pool_initial_tao: Balance  # Initial TAO in the pool
    burned_amount: Balance  # Amount burned for this subnet
    
    # Metadata
    created_at: int  # Block timestamp when subnet was created
    is_active: bool  # Whether the subnet is active
    
    # Subnet details
    name: str  # Subnet name
    description: str  # Subnet description
    
    # Additional market data (from getSubnetDetails)
    current_price: Optional[Balance] = None
    total_volume: Optional[Balance] = None
    hetu_reserve: Optional[Balance] = None
    alpha_reserve: Optional[Balance] = None
    
    @classmethod
    def from_contract_data(cls, subnet_info_tuple: tuple, market_data: Optional[tuple] = None) -> "EVMSubnetInfo":
        """
        Creates an EVMSubnetInfo object from contract data.
        
        Args:
            subnet_info_tuple: The subnet info tuple from the contract
            market_data: Optional tuple containing (current_price, total_volume, hetu_reserve, alpha_reserve)
            
        Returns:
            EVMSubnetInfo: The parsed subnet information
        """
        # Parse subnet info tuple
        netuid = subnet_info_tuple[0]
        owner = subnet_info_tuple[1]
        alpha_token = subnet_info_tuple[2]
        amm_pool = subnet_info_tuple[3]
        locked_amount = Balance(subnet_info_tuple[4])
        pool_initial_tao = Balance(subnet_info_tuple[5])
        burned_amount = Balance(subnet_info_tuple[6])
        created_at = subnet_info_tuple[7]
        is_active = subnet_info_tuple[8]
        name = subnet_info_tuple[9]
        description = subnet_info_tuple[10]
        
        # Parse market data if provided
        current_price = None
        total_volume = None
        hetu_reserve = None
        alpha_reserve = None
        
        if market_data:
            current_price = Balance(market_data[0])
            total_volume = Balance(market_data[1])
            hetu_reserve = Balance(market_data[2])
            alpha_reserve = Balance(market_data[3])
        
        return cls(
            netuid=netuid,
            owner=owner,
            alpha_token=alpha_token,
            amm_pool=amm_pool,
            locked_amount=locked_amount,
            pool_initial_tao=pool_initial_tao,
            burned_amount=burned_amount,
            created_at=created_at,
            is_active=is_active,
            name=name,
            description=description,
            current_price=current_price,
            total_volume=total_volume,
            hetu_reserve=hetu_reserve,
            alpha_reserve=alpha_reserve,
        )
    
    def to_dict(self) -> dict:
        """Converts the EVMSubnetInfo to a dictionary."""
        return {
            "netuid": self.netuid,
            "owner": self.owner,
            "alpha_token": self.alpha_token,
            "amm_pool": self.amm_pool,
            "locked_amount": self.locked_amount.tao,
            "pool_initial_tao": self.pool_initial_tao.tao,
            "burned_amount": self.burned_amount.tao,
            "created_at": self.created_at,
            "is_active": self.is_active,
            "name": self.name,
            "description": self.description,
            "current_price": self.current_price.tao if self.current_price else None,
            "total_volume": self.total_volume.tao if self.total_volume else None,
            "hetu_reserve": self.hetu_reserve.tao if self.hetu_reserve else None,
            "alpha_reserve": self.alpha_reserve.tao if self.alpha_reserve else None,
        } 
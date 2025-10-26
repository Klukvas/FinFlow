"""shorten_long_mcc_names

Revision ID: 3207794d8134
Revises: seed_mcc_translations
Create Date: 2025-10-26 19:12:34.620278

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3207794d8134'
down_revision: Union[str, None] = 'seed_mcc_translations'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Shorten long MCC code names to under 100 characters."""
    # MCC 1740: 142 -> 65 chars
    op.execute("""
        UPDATE mcc_codes 
        SET name = 'Insulation, Masonry, Stonework, Plastering Contractors' 
        WHERE mcc_code = 1740;
    """)
    
    # MCC 5961: 120 -> 41 chars
    op.execute("""
        UPDATE mcc_codes 
        SET name = 'Mail Order Houses, Book/Record Clubs' 
        WHERE mcc_code = 5961;
    """)
    
    # MCC 4214: 111 -> 68 chars
    op.execute("""
        UPDATE mcc_codes 
        SET name = 'Motor Freight, Moving, Storage, Trucking, Delivery Services' 
        WHERE mcc_code = 4214;
    """)
    
    # MCC 1711: 105 -> 71 chars
    op.execute("""
        UPDATE mcc_codes 
        SET name = 'Air Conditioning, Heating Contractors - Sales, Service, Installation' 
        WHERE mcc_code = 1711;
    """)
    
    # MCC 6051: 101 -> 88 chars
    op.execute("""
        UPDATE mcc_codes 
        SET name = 'Non-Financial Institutions - Foreign Currency, Money Orders, Travelers Checks' 
        WHERE mcc_code = 6051;
    """)
    
    # MCC 7995: 101 -> 60 chars
    op.execute("""
        UPDATE mcc_codes 
        SET name = 'Betting - Lottery, Casino Gaming, Off-track, Race Tracks' 
        WHERE mcc_code = 7995;
    """)
    
    # MCC 4111: 97 -> 65 chars
    op.execute("""
        UPDATE mcc_codes 
        SET name = 'Local/Suburban Commuter - Railroads, Ferries, Water Transportation' 
        WHERE mcc_code = 4111;
    """)

def downgrade() -> None:
    """Restore original long MCC code names."""
    op.execute("""
        UPDATE mcc_codes 
        SET name = 'Insulation – Contractors, Masonry, Stonework Contractors, Plastering Contractors, Stonework and Masonry Contractors, Tile Settings Contractors' 
        WHERE mcc_code = 1740;
    """)
    
    op.execute("""
        UPDATE mcc_codes 
        SET name = 'Mail Order Houses Including Catalog Order Stores, Book/Record Clubs (No longer permitted for U.S. original presentments)' 
        WHERE mcc_code = 5961;
    """)
    
    op.execute("""
        UPDATE mcc_codes 
        SET name = 'Motor Freight Carriers, Moving and Storage Companies, Trucking – Local/Long Distance, Delivery Services – Local' 
        WHERE mcc_code = 4214;
    """)
    
    op.execute("""
        UPDATE mcc_codes 
        SET name = 'Air Conditioning Contractors – Sales and Installation, Heating Contractors – Sales, Service, Installation' 
        WHERE mcc_code = 1711;
    """)
    
    op.execute("""
        UPDATE mcc_codes 
        SET name = 'Non-Financial Institutions – Foreign Currency, Money Orders (not wire transfer) and Travelers Cheques' 
        WHERE mcc_code = 6051;
    """)
    
    op.execute("""
        UPDATE mcc_codes 
        SET name = 'Betting (including Lottery Tickets, Casino Gaming Chips, Off-track Betting and Wagers at Race Tracks)' 
        WHERE mcc_code = 7995;
    """)
    
    op.execute("""
        UPDATE mcc_codes 
        SET name = 'Local/Suburban Commuter Passenger Transportation – Railroads, Feries, Local Water Transportation.' 
        WHERE mcc_code = 4111;
    """)

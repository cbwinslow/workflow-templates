from typing import Dict, List
import logging
import trello
from trello import TrelloClient as TrelloAPI

logger = logging.getLogger('trello_client')
class TrelloIntegration:
    def __init__(self, api_key: str, token: str):
        """Initialize Trello client."""
        self.client = TrelloAPI(
            api_key=api_key,
            token=token
        )
    
    def create_board(self, board_name: str) -> str:
        """Create a new Trello board."""
        try:
            board = self.client.add_board(board_name)
            logger.info(f"Created Trello board: {board_name}")
            return board.id
        except Exception as e:
            logger.error(f"Failed to create Trello board: {str(e)}")
            raise
    
    def create_lists(self, board_id: str, list_names: List[str]) -> Dict[str, str]:
        """Create lists on the board."""
        try:
            board = self.client.get_board(board_id)
            list_ids = {}
            for name in list_names:
                trello_list = board.add_list(name)
                list_ids[name] = trello_list.id
            return list_ids
        except Exception as e:
            logger.error(f"Failed to create Trello lists: {str(e)}")
            raise
    
    def create_card(self, list_id: str, title: str, description: str = "", labels: List[str] = None) -> str:
        """Create a card in the specified list."""
        try:
            trello_list = self.client.get_list(list_id)
            card = trello_list.add_card(
                name=title,
                desc=description
            )
            if labels:
                for label in labels:
                    card.add_label(label)
            return card.id
        except Exception as e:
            logger.error(f"Failed to create Trello card: {str(e)}")
            raise


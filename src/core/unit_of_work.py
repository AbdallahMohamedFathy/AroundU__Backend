from sqlalchemy.orm import Session
from src.core.database import SessionLocal
from src.repositories.user_repository import UserRepository
from src.repositories.place_repository import PlaceRepository
from src.repositories.review_repository import ReviewRepository
from src.repositories.favorite_repository import FavoriteRepository
from src.repositories.chat_message_repository import ChatMessageRepository
from src.repositories.conversation_repository import ConversationRepository
from src.repositories.message_repository import MessageRepository
from src.repositories.search_repository import SearchRepository
from src.repositories.category_repository import CategoryRepository
from src.repositories.place_image_repository import PlaceImageRepository
from src.repositories.item_repository import ItemRepository
from src.repositories.interaction_repository import InteractionRepository

class UnitOfWork:
    """
    Unit of Work patterns manages transaction and repository lifecycles.
    Ensures that all operations within the context either fail together or succeed together.
    """
    
    def __init__(self, session_factory):
        self.session_factory = session_factory

    def __enter__(self):
        self.session = self.session_factory()
        
        # Initialize repositories with the transactional session
        self.user_repository = UserRepository(self.session)
        self.place_repository = PlaceRepository(self.session)
        self.review_repository = ReviewRepository(self.session)
        self.favorite_repository = FavoriteRepository(self.session)
        self.category_repository = CategoryRepository(self.session)
        self.place_image_repository = PlaceImageRepository(self.session)
        self.chat_message_repository = ChatMessageRepository(self.session)
        self.conversation_repository = ConversationRepository(self.session)
        self.message_repository = MessageRepository(self.session)
        self.search_repository = SearchRepository(self.session)
        self.item_repository = ItemRepository(self.session)
        self.interaction_repository = InteractionRepository(self.session)
        
        return self

    def commit(self):
        self.session.commit()

    def rollback(self):
        self.session.rollback()

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self.rollback()
        self.session.close()

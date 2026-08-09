from app.services.embedding_service import EmbeddingService
from dotenv import load_dotenv
load_dotenv()

def main():
    service = EmbeddingService()

    text = """
    我是一名中階羽球玩家，
    主要打法是進攻型，
    喜歡後場殺球，
    預算約 5000 元。
    """

    vector = service.embed_query(text)

    print("Embedding API call succeeded.")
    print("Vector dimension:", len(vector))
    print("First 10 values:", vector[:10])


if __name__ == "__main__":
    main()
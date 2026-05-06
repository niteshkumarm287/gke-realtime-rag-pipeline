from vertexai import rag
import vertexai

vertexai.init(project="game-d8160", location="asia-south1")
rag.delete_corpus(name="projects/game-d8160/locations/asia-south1/ragCorpora/5764607523034234880")

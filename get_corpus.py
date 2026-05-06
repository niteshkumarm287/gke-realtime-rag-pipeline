from vertexai.preview import rag
import vertexai

# Initialize with your project and restricted region
vertexai.init(project="game-d8160", location="asia-south1")

# List all corpora to find yours
corpora = rag.list_corpora()

for corpus in corpora:
    print(f"Display Name: {corpus.display_name}")
    print(f"Full Resource Name: {corpus.name}") # This contains the ID at the end

import json
import dashscope
from dashscope import TextEmbedding
from dashvector import Client, Doc
from config import DASHSCOPE_API_KEY, DASHVECTOR_API_KEY, DASHVECTOR_ENDPOINT, COLLECTION_NAME, EMBEDDING_DIMENSION


class DiscoveryService:
    def __init__(self):
        """Initialize DashScope and DashVector clients, and prepare the collection."""
        # Set API keys
        dashscope.api_key = DASHSCOPE_API_KEY
        
        # Initialize DashVector client
        self.client = Client(
            api_key=DASHVECTOR_API_KEY,
            endpoint=DASHVECTOR_ENDPOINT
        )
        
        # Get or create collection
        try:
            self.collection = self.client.get(COLLECTION_NAME)
        except Exception:
            # If collection doesn't exist, create it
            rsp = self.client.create(COLLECTION_NAME, EMBEDDING_DIMENSION)
            if not rsp:
                raise Exception("Failed to create DashVector collection")
            self.collection = self.client.get(COLLECTION_NAME)
            if not self.collection:
                raise Exception("Failed to get DashVector collection after creation")

    def _generate_embedding(self, text):
        """Generate embedding for text using DashScope's text-embedding-v4 model."""
        rsp = TextEmbedding.call(
            model=TextEmbedding.Models.text_embedding_v4,
            input=text
        )
        if rsp.status_code != 200:
            raise Exception(f"Failed to generate embedding: {rsp.message}")
        embeddings = [record['embedding'] for record in rsp.output['embeddings']]
        return embeddings[0] if isinstance(text, str) else embeddings

    def add_server(self, server_name, server_description, server_endpoint, tools):
        """
        Add a new MCP server to the discovery service.
        
        Args:
            server_name (str): Unique name of the server
            server_description (str): Description of the server
            server_endpoint (str): Endpoint URL of the server
            tools (str): JSON string representation of tools list
        """
        # Generate vector for the server description
        service_vector = self._generate_embedding(server_description)
        
        # Prepare metadata (tools must be a string for DashVector)
        service_metadata = {
            "server_description": server_description,
            "server_endpoint": server_endpoint,
            "tools": tools  # Already serialized as JSON string
        }
        
        # Insert into DashVector using server_name as the document ID
        rsp = self.collection.insert(
            Doc(id=server_name, vector=service_vector, fields=service_metadata)
        )
        
        if not rsp:
            raise Exception(f"Failed to insert server '{server_name}' into DashVector")
        
        return {"status": "success", "message": f"Server '{server_name}' registered."}

    def search_server(self, query, top_k=3):
        """
        Search for MCP servers based on a query.
        
        Args:
            query (str): Search query
            top_k (int): Number of top results to return (default: 3)
            
        Returns:
            list: List of matching servers with their metadata
        """
        # Generate vector for the query
        query_vector = self._generate_embedding(query)
        
        # Perform vector search
        rsp = self.collection.query(
            query_vector,
            topk=top_k,
            output_fields=['server_description', 'server_endpoint', 'tools']
        )
        
        if not rsp:
            raise Exception("Failed to query DashVector")
        
        # Process results
        results = []
        for doc in rsp.output:
            results.append({
                "server_name": doc.id,
                "server_description": doc.fields['server_description'],
                "server_endpoint": doc.fields['server_endpoint'],
                "tools": doc.fields['tools'],  # Still a JSON string
                "score": doc.score
            })
        
        return results

    def get_server_endpoint(self, server_name):
        """
        Get the endpoint of a specific server by name.
        
        Args:
            server_name (str): Name of the server
            
        Returns:
            str: Endpoint URL of the server
        """
        # Search for the server by name using search_server
        # This is the most reliable method given the DashVector implementation
        try:
            # Use a search query that should match the server name
            results = self.search_server(server_name, 20)  # Search for up to 20 matches
            
            # Find the exact match
            for result in results:
                if result["server_name"] == server_name:
                    return result["server_endpoint"]
                    
            # If not found in first search, try a more general search
            # and look for exact name match
            general_results = self.search_server("", 100)  # Search all with empty query
            for result in general_results:
                if result["server_name"] == server_name:
                    return result["server_endpoint"]
        except Exception as e:
            pass  # Continue to raise exception
            
        raise Exception(f"Server '{server_name}' not found")
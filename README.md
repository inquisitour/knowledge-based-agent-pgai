# knowledge-based-agent-pgai

Welcome to the **AI-Powered FAQ Chatbot** project! This chatbot leverages advanced vector search capabilities and in-database AI processing to deliver accurate and responsive answers to user queries. Built using PostgreSQL extensions like **pgvector**, **pgvectorscale**, and **pgai**, and deployed on AWS with **AWS Lambda** and **AWS Lex**, this solution is designed for scalability, efficiency, and seamless user interactions.

## 🛠️ Project Overview

The FAQ chatbot is designed to handle user queries by:
1. Transforming the input text into high-dimensional embeddings using AI models.
2. Storing and managing these embeddings directly within PostgreSQL using `pgvector`.
3. Performing optimized similarity searches with `pgvectorscale` for fast, scalable retrieval.
4. Utilizing `pgai` for in-database embedding generation, reducing latency and simplifying the workflow.

## ⚙️ Technologies and Tools Used

- **PostgreSQL**: Core relational database with advanced extensions.
  - **pgvector**: For efficient vector storage and similarity search.
  - **pgvectorscale**: For scalable, high-performance indexing and vector search using StreamingDiskANN.
  - **pgai**: For embedding generation and AI-based query handling directly within the database.
- **AWS Lambda**: Serverless backend execution for processing chatbot requests.
- **AWS Lex**: Conversational interface providing natural language understanding.
- **AWS S3**: Storage of FAQ data files, enabling dynamic updates.
- **OpenAI Embeddings**: Used initially for vector transformation before transitioning to in-database embedding generation with `pgai`.

## 🏗️ Project Architecture

```text
User Query → AWS Lex → AWS Lambda (Fulfillment Codehook) → PostgreSQL Database
                 ↳ pgvector (Vector Storage)
                 ↳ pgvectorscale (Optimized Search)
                 ↳ pgai (Embedding Generation)
```

1. **User Query**: User inputs a question into the AWS Lex chatbot.
2. **AWS Lambda**: The query is passed to AWS Lambda for backend processing.
3. **PostgreSQL**: The backend interacts with PostgreSQL, utilizing vector search to find similar questions and retrieve the best answer.
4. **Response**: The retrieved answer is returned to the user via AWS Lex.

## 📝 Features

- **High-Performance Vector Search**: Leverages `pgvector` and `pgvectorscale` for efficient similarity search operations.
- **In-Database AI Capabilities**: Uses `pgai` for real-time embedding generation directly within PostgreSQL.
- **Scalable Architecture**: Deployed using AWS services, ensuring seamless scalability and reliability.
- **Dynamic Data Updates**: Supports dynamic updates to the FAQ dataset using AWS S3.

## 🚀 Getting Started

### Prerequisites

- **PostgreSQL 15+** with `pgvector`, `pgvectorscale`, and `pgai` extensions installed.
- **AWS Account** with access to AWS Lambda, AWS Lex, and AWS S3.
- **Python 3.8+** environment with required dependencies installed.

### Installation

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/your-username/your-repo-name.git
   cd your-repo-name
   ```

2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Set Up PostgreSQL**:
   - Enable the required extensions:
     ```sql
     CREATE EXTENSION IF NOT EXISTS pgvector;
     CREATE EXTENSION IF NOT EXISTS pgvectorscale;
     CREATE EXTENSION IF NOT EXISTS pgai;
     ```

4. **Configure AWS Lambda**:
   - Deploy the `data_processing.py` and `agent.py` scripts as AWS Lambda functions.
   - Link the Lambda function as a fulfillment codehook for your AWS Lex chatbot.

5. **Upload FAQ Data to AWS S3**:
   - Store your FAQ dataset (CSV format) in an S3 bucket.
   - Ensure the bucket and file permissions allow access to your Lambda function.

### Usage

- Interact with the chatbot via AWS Lex, and it will return the most relevant answer based on vector similarity search and AI processing.
- You can update the FAQ dataset by uploading a new file to the specified S3 bucket. The changes will be automatically reflected in the chatbot responses.

## 🧪 Testing

- You can test the chatbot using the AWS Lex test console or integrate it with your web application using the AWS SDK.
- For local testing, use the `test_query.py` script provided in the repository:
  ```bash
  python test_query.py "What is the refund policy?"
  ```

## 📈 Performance Optimization

- **pgvectorscale**: The use of StreamingDiskANN improves search performance on large datasets.
- **pgai Integration**: In-database embedding generation reduces the need for external API calls, lowering latency.

## 🤖 Future Enhancements

- **Multi-Language Support**: Extend the chatbot capabilities to support multiple languages using language-specific embeddings.
- **Improved FAQ Dataset Management**: Add a web interface for easy updates and monitoring of the FAQ dataset.
- **Advanced AI Models**: Integrate more sophisticated AI models for better understanding and handling of complex queries.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit issues, fork the repository, and open pull requests.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙌 Acknowledgments

- Special thanks to the developers of **pgvector**, **pgvectorscale**, and **pgai** for their powerful extensions.
- Thanks to **AWS** for providing the infrastructure that made this project scalable and reliable.

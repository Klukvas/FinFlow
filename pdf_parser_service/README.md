# PDF Parser Service

A microservice for parsing bank PDF statements and extracting transaction data.

## Architecture

The service uses an abstract parser pattern with specific implementations for each bank:

```
BasePDFParser (Abstract)
├── MonobankParser
├── PrivatbankParser  
├── UkrsibbankParser
├── RaiffeisenParser
├── OTPParser
└── UniversalParser
```

## Supported Banks

- **Monobank** - Full support with table parsing
- **Privatbank** - Basic support
- **Ukrsibbank** - Basic support  
- **Raiffeisen** - Basic support
- **OTP** - Basic support
- **Universal** - Fallback parser for unknown formats

## Features

- ✅ **Multi-bank Support** - Dedicated parsers for each bank
- ✅ **Auto-detection** - Automatically detects bank type from PDF content
- ✅ **Table Extraction** - Uses pdfplumber for accurate table parsing
- ✅ **Confidence Scoring** - Each transaction gets a confidence score
- ✅ **Error Handling** - Comprehensive error handling and logging
- ✅ **Docker Support** - Ready for containerized deployment

## API Endpoints

### Parse PDF
```http
POST /pdf/parse
Content-Type: multipart/form-data

file: <PDF file>
bank_type: monobank (optional)
user_id: 1
```

### Get Supported Banks
```http
GET /pdf/supported-banks
```

### Health Check
```http
GET /pdf/health
```

## Usage

### Docker Compose
```bash
docker-compose up pdf_parser_service
```

### Direct Testing
```bash
cd pdf_parser_service
python test_monobank.py
```

## Example Response

```json
{
  "transactions": [
    {
      "amount": 25.50,
      "description": "Domino's Pizza",
      "date": "2025-09-28",
      "transaction_type": "expense",
      "bank_type": "monobank",
      "confidence_score": 0.9,
      "raw_text": "28.09.2025 21:47:52 | Domino's Pizza | -25.50"
    }
  ],
  "bank_detected": "monobank",
  "total_transactions": 1,
  "parsing_metadata": {
    "file_size": 1024000,
    "parsing_method": "monobank_parser",
    "confidence_threshold": 0.7
  }
}
```

## Development

### Adding New Bank Parser

1. Create new parser class inheriting from `BasePDFParser`
2. Implement required abstract methods
3. Add to `__init__.py` exports
4. Register in `PDFParserService.bank_parsers`

### Testing

```bash
# Test specific bank parser
python test_monobank.py

# Test with Docker
docker-compose up pdf_parser_service
curl -X POST http://localhost:8007/pdf/parse \
  -F "file=@test.pdf" \
  -F "user_id=1"
```

## Configuration

Environment variables:
- `MAX_FILE_SIZE` - Maximum file size (default: 10MB)
- `SUPPORTED_BANKS` - Comma-separated list of supported banks
- `LOG_LEVEL` - Logging level (default: INFO)

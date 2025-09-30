# PDF Parser API Client

This directory contains the API client for the PDF Parser service, which allows users to upload bank PDF statements and automatically extract transaction data.

## Features

- **PDF Upload & Parsing**: Upload PDF files and extract transaction data
- **Multi-language Support**: Support for Ukrainian and English bank statements
- **Bank Detection**: Automatic detection of bank type from PDF content
- **Transaction Validation**: Review and edit parsed transactions before creating records
- **Language Management**: Get available languages for each supported bank

## Supported Banks

Currently supported:
- **Monobank** (Ukrainian and English)

## API Client Usage

### Basic Setup

```typescript
import { PDFParserApiClient } from '@/services/api/pdfParserApiClient';
import { useApiClients } from '@/hooks/useApiClients';

// Using the hook (recommended)
const { pdfParser } = useApiClients();

// Or direct instantiation
const client = new PDFParserApiClient(getToken, refreshToken);
```

### Core Methods

#### 1. Parse PDF File

```typescript
const response = await pdfParser.parsePDF(file, 'monobank');
if ('error' in response) {
  console.error('Error:', response.error);
} else {
  console.log('Transactions:', response.transactions);
  console.log('Bank detected:', response.bank_detected);
}
```

#### 2. Get Supported Banks

```typescript
const response = await pdfParser.getSupportedBanks();
if ('error' in response) {
  console.error('Error:', response.error);
} else {
  console.log('Supported banks:', response.supported_banks);
}
```

#### 3. Get Bank Languages

```typescript
const response = await pdfParser.getBankLanguages('monobank');
if ('error' in response) {
  console.error('Error:', response.error);
} else {
  console.log('Available languages:', response.available_languages);
}
```

#### 4. Get All Languages

```typescript
const response = await pdfParser.getAllLanguages();
if ('error' in response) {
  console.error('Error:', response.error);
} else {
  console.log('All bank languages:', response.banks);
}
```

### Utility Methods

#### Check if Bank is Supported

```typescript
const isSupported = await pdfParser.isBankSupported('monobank');
console.log('Monobank supported:', isSupported);
```

#### Get Comprehensive Bank Info

```typescript
const bankInfo = await pdfParser.getBankInfo('monobank');
if ('error' in bankInfo) {
  console.error('Error:', bankInfo.error);
} else {
  console.log('Bank info:', bankInfo);
  console.log('Languages:', bankInfo.available_languages);
  console.log('Supported banks:', bankInfo.supported_banks);
}
```

#### Health Check

```typescript
const health = await pdfParser.healthCheck();
if ('error' in health) {
  console.error('Service error:', health.error);
} else {
  console.log('Service status:', health.status);
}
```

## Data Types

### ParsedTransaction

```typescript
interface ParsedTransaction {
  amount: number;
  description: string;
  transaction_date: string;
  transaction_type: 'income' | 'expense';
  bank_type: string;
  raw_text?: string;
  confidence_score: number;
}
```

### TransactionValidation

```typescript
interface TransactionValidation {
  transaction_id: string;
  amount: number;
  description: string;
  transaction_date: string;
  transaction_type: 'income' | 'expense';
  category_id?: number;
  is_valid: boolean;
}
```

### LanguageInfo

```typescript
interface LanguageInfo {
  code: string;
  name: string;
  headers_count: number;
}
```

## Error Handling

All API methods return either the expected data or an `ApiError` object:

```typescript
const response = await pdfParser.parsePDF(file);
if ('error' in response) {
  // Handle error
  console.error('API Error:', response.error);
} else {
  // Handle success
  console.log('Data:', response);
}
```

## Example: Complete PDF Processing Flow

```typescript
import { useApiClients } from '@/hooks/useApiClients';

const MyComponent = () => {
  const { pdfParser, income, expense } = useApiClients();

  const handleFileUpload = async (file: File) => {
    try {
      // 1. Parse PDF
      const parseResponse = await pdfParser.parsePDF(file, 'monobank');
      if ('error' in parseResponse) {
        throw new Error(parseResponse.error);
      }

      // 2. Review transactions (in UI)
      const transactions = parseResponse.transactions;
      console.log('Parsed transactions:', transactions);

      // 3. Create income/expense records
      for (const transaction of transactions) {
        if (transaction.transaction_type === 'income') {
          await income.createIncome({
            amount: transaction.amount,
            description: transaction.description,
            date: transaction.transaction_date,
            category_id: undefined
          });
        } else {
          await expense.createExpense({
            amount: transaction.amount,
            description: transaction.description,
            date: transaction.transaction_date,
            category_id: 1 // Default category
          });
        }
      }

      console.log('All transactions created successfully!');
    } catch (error) {
      console.error('Error processing PDF:', error);
    }
  };

  return (
    <div>
      <input
        type="file"
        accept=".pdf"
        onChange={(e) => {
          const file = e.target.files?.[0];
          if (file) handleFileUpload(file);
        }}
      />
    </div>
  );
};
```

## Configuration

The API client uses the configuration from `@/config/env.ts`:

```typescript
// Environment configuration
export const config = {
  api: {
    pdfParserServiceUrl: import.meta.env.VITE_PDF_PARSER_SERVICE_URL || 'http://localhost:8007',
  },
  // ... other config
};
```

## Testing

See `pdfParserApiClient.test.ts` for example usage and testing patterns.

## Notes

- The PDF parser service currently only supports Monobank
- All API calls require authentication (handled by AuthHttpClient)
- File uploads are limited to 10MB by default
- The service automatically detects the bank type if not specified
- Transaction confidence scores range from 0.0 to 1.0

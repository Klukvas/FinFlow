/**
 * Example usage of PDFParserApiClient
 * This file demonstrates how to use the PDF parser API client
 */

import { PDFParserApiClient } from './pdfParserApiClient';

// Mock token functions for testing
const mockGetToken = () => 'mock-token';
const mockRefreshToken = async () => true;

// Example usage
export const exampleUsage = async () => {
  const client = new PDFParserApiClient(mockGetToken, mockRefreshToken);

  try {
    // Get supported banks
    console.log('Getting supported banks...');
    const banksResponse = await client.getSupportedBanks();
    console.log('Supported banks:', banksResponse);

    // Get languages for Monobank
    console.log('Getting Monobank languages...');
    const languagesResponse = await client.getBankLanguages('monobank');
    console.log('Monobank languages:', languagesResponse);

    // Get all languages
    console.log('Getting all languages...');
    const allLanguagesResponse = await client.getAllLanguages();
    console.log('All languages:', allLanguagesResponse);

    // Check if a bank is supported
    console.log('Checking if Monobank is supported...');
    const isSupported = await client.isBankSupported('monobank');
    console.log('Monobank supported:', isSupported);

    // Get comprehensive bank info
    console.log('Getting comprehensive bank info...');
    const bankInfo = await client.getBankInfo('monobank');
    console.log('Bank info:', bankInfo);

    // Health check
    console.log('Checking service health...');
    const healthResponse = await client.healthCheck();
    console.log('Health status:', healthResponse);

  } catch (error) {
    console.error('Error using PDF parser API client:', error);
  }
};

// Example of parsing a PDF file
export const exampleParsePDF = async (file: File) => {
  const client = new PDFParserApiClient(mockGetToken, mockRefreshToken);

  try {
    console.log('Parsing PDF file:', file.name);
    const response = await client.parsePDF(file, 'monobank');
    
    if ('error' in response) {
      console.error('PDF parsing error:', response.error);
      return;
    }

    console.log('PDF parsing successful!');
    console.log('Bank detected:', response.bank_detected);
    console.log('Total transactions:', response.total_transactions);
    console.log('Successful parses:', response.successful_parses);
    console.log('Failed parses:', response.failed_parses);
    console.log('Transactions:', response.transactions);

    return response;
  } catch (error) {
    console.error('Error parsing PDF:', error);
  }
};

// Export for use in other files
export { PDFParserApiClient };

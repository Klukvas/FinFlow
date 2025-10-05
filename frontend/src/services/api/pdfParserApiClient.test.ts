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
    const banksResponse = await client.getSupportedBanks();

    // Get languages for Monobank
    const languagesResponse = await client.getBankLanguages('monobank');

    // Get all languages
    const allLanguagesResponse = await client.getAllLanguages();

    // Check if a bank is supported
    const isSupported = await client.isBankSupported('monobank');

    // Get comprehensive bank info
    const bankInfo = await client.getBankInfo('monobank');

    // Health check
    const healthResponse = await client.healthCheck();

  } catch (error) {
    console.error('Error using PDF parser API client:', error);
  }
};

// Example of parsing a PDF file
export const exampleParsePDF = async (file: File) => {
  const client = new PDFParserApiClient(mockGetToken, mockRefreshToken);

  try {
    const response = await client.parsePDF(file, 'monobank');
    
    if ('error' in response) {
      console.error('PDF parsing error:', response.error);
      return;
    }


    return response;
  } catch (error) {
    console.error('Error parsing PDF:', error);
  }
};

// Export for use in other files
export { PDFParserApiClient };

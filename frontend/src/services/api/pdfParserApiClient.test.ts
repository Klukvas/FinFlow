/**
 * Example usage of PDFParserApiClient
 * This file demonstrates how to use the PDF parser API client
 */

import { PDFParserApiClient } from "./pdfParserApiClient";

// Mock token functions for testing
const mockGetToken = () => "mock-token";
const mockRefreshToken = async () => true;

// Example usage
export const exampleUsage = async () => {
  const client = new PDFParserApiClient(mockGetToken, mockRefreshToken);

  try {
    // Get supported banks
    await client.getSupportedBanks();

    // Get languages for Monobank
    await client.getBankLanguages("monobank");

    // Get all languages
    await client.getAllLanguages();

    // Check if a bank is supported
    await client.isBankSupported("monobank");

    // Get comprehensive bank info
    await client.getBankInfo("monobank");

    // Health check
    await client.healthCheck();
  } catch (error) {
    console.error("Error using PDF parser API client:", error);
  }
};

// Example of parsing a PDF file
export const exampleParsePDF = async (file: File) => {
  const client = new PDFParserApiClient(mockGetToken, mockRefreshToken);

  try {
    // Parse PDF with language parameter
    const response = await client.parsePDF(file, "monobank", "ru");

    if ("error" in response) {
      console.error("PDF parsing error:", response.error);
      return;
    }

    return response;
  } catch (error) {
    console.error("Error parsing PDF:", error);
    return undefined;
  }
};

// Export for use in other files
export { PDFParserApiClient };

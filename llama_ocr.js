import { ocr } from 'llama-ocr';
import fs from 'fs';

const processImage = async (filePath) => {
  try {
    console.log('Processing image...');
    const markdown = await ocr({
      filePath,
      apiKey: process.env.TOGETHER_API_KEY,
    });
    console.log('OCR Result:\n', markdown);
  } catch (error) {
    console.error('Error during OCR processing:', error);
  }
};

// Get the image path from the command-line arguments
const filePath = process.argv[2];
if (!filePath) {
  console.error('Please provide the path to an image as a command-line argument.');
  process.exit(1);
}

// Run the OCR process
processImage(filePath);

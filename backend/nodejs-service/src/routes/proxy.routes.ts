import { Router } from 'express';
import axios from 'axios';

const router = Router();
const FASTAPI_URL = process.env.FASTAPI_URL || 'http://localhost:8000';

router.post('/recommendations', async (req, res) => {
  try {
    const response = await axios.post(`${FASTAPI_URL}/api/v1/recommendations/recommend`, req.body);
    res.json(response.data);
  } catch (error) {
    res.status(500).json({ error: 'AI service unavailable' });
  }
});

router.post('/ocr/scan', async (req, res) => {
  try {
    const response = await axios.post(`${FASTAPI_URL}/api/v1/ocr/scan`, req.body, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
    res.json(response.data);
  } catch (error) {
    res.status(500).json({ error: 'OCR service unavailable' });
  }
});

export default router;

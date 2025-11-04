import { Router } from 'express';
import { authenticate } from '../middleware/auth.middleware';

const router = Router();

router.get('/profile', authenticate, async (req, res) => {
  res.json({ message: 'User profile endpoint' });
});

export default router;

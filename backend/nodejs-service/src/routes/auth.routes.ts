import { Router } from 'express';
import bcrypt from 'bcrypt';
import jwt from 'jsonwebtoken';
import { AppDataSource } from '../config/database';
import { User } from '../entities/User';

const router = Router();
const userRepository = AppDataSource.getRepository(User);

router.post('/register', async (req, res) => {
  try {
    const { email, username, password } = req.body;
    const hashedPassword = await bcrypt.hash(password, 10);
    const user = userRepository.create({
      email,
      username,
      password_hash: hashedPassword
    });
    await userRepository.save(user);
    res.status(201).json({ success: true, userId: user.id });
  } catch (error) {
    res.status(400).json({ error: 'Registration failed' });
  }
});

router.post('/login', async (req, res) => {
  try {
    const { email, password } = req.body;
    const user = await userRepository.findOne({ where: { email } });
    if (!user || !await bcrypt.compare(password, user.password_hash)) {
      return res.status(401).json({ error: 'Invalid credentials' });
    }
    const token = jwt.sign({ userId: user.id }, process.env.JWT_SECRET || 'secret', { expiresIn: '24h' });
    res.json({ success: true, token, user: { id: user.id, email: user.email, username: user.username } });
  } catch (error) {
    res.status(500).json({ error: 'Login failed' });
  }
});

export default router;

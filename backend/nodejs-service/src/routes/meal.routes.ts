import { Router } from 'express';
import { AppDataSource } from '../config/database';
import { Meal } from '../entities/Meal';

const router = Router();
const mealRepository = AppDataSource.getRepository(Meal);

router.get('/', async (req, res) => {
  try {
    const meals = await mealRepository.find();
    res.json({ success: true, meals });
  } catch (error) {
    res.status(500).json({ error: 'Failed to fetch meals' });
  }
});

router.get('/:id', async (req, res) => {
  try {
    const meal = await mealRepository.findOne({ where: { id: req.params.id } });
    if (!meal) {
      return res.status(404).json({ error: 'Meal not found' });
    }
    res.json({ success: true, meal });
  } catch (error) {
    res.status(500).json({ error: 'Failed to fetch meal' });
  }
});

export default router;

import { describe, it, expect } from 'vitest';

const formatDuration = (seconds) => {
  const mins = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);
  return `${mins}:${secs < 10 ? '0' : ''}${secs}`;
};

const isValidEmail = (email) => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);

describe('Проверка логики аудиоплеера и формы букинга', () => {
  it('корректно форматирует длительность трека в мм:сс', () => {
    expect(formatDuration(185)).toBe('3:05');
    expect(formatDuration(45)).toBe('0:45');
  });

  it('валидирует корректный и некорректный email в форме', () => {
    expect(isValidEmail('booking@fest.ru')).toBe(true);
    expect(isValidEmail('invalid-email.ru')).toBe(false);
  });
});
using System.Collections.Generic;
using UnityEngine;

namespace WaterSort.Core
{
    public static class LevelGenerator
    {
        public static (int colors, int empties) GetDifficulty(int level)
        {
            if (level <= 3) return (3, 2);
            if (level <= 8) return (4, 2);
            if (level <= 15) return (5, 2);
            if (level <= 25) return (6, 2);
            if (level <= 40) return (7, 2);
            if (level <= 60) return (8, 2);
            return (9, 2);
        }

        public static string GetDifficultyName(int level)
        {
            var (c, _) = GetDifficulty(level);
            switch (c)
            {
                case 3: return "EASY";
                case 4: return "NORMAL";
                case 5: return "MEDIUM";
                case 6: return "HARD";
                case 7: return "EXPERT";
                case 8: return "MASTER";
                default: return "INSANE";
            }
        }

        public static List<List<int>> Generate(int level)
        {
            var (numColors, numEmpty) = GetDifficulty(level);
            var rng = new System.Random(level * 31337 + 97);

            int[] pool = new int[numColors * 4];
            for (int c = 0; c < numColors; c++)
                for (int j = 0; j < 4; j++)
                    pool[c * 4 + j] = c + 1;

            List<List<int>> tubes = null;

            for (int attempt = 0; attempt < 300; attempt++)
            {
                Shuffle(pool, rng);
                tubes = new List<List<int>>();

                bool anySolved = false;
                for (int i = 0; i < numColors; i++)
                {
                    var tube = new List<int>();
                    for (int j = 0; j < 4; j++)
                        tube.Add(pool[i * 4 + j]);
                    tubes.Add(tube);

                    if (IsComplete(tube)) anySolved = true;
                }

                if (!anySolved) break;
            }

            for (int i = 0; i < numEmpty; i++)
                tubes.Add(new List<int>());

            return tubes;
        }

        public static bool IsComplete(List<int> tube)
        {
            if (tube.Count != 4) return false;
            return tube[0] == tube[1] && tube[1] == tube[2] && tube[2] == tube[3];
        }

        public static bool AllComplete(List<List<int>> tubes)
        {
            foreach (var t in tubes)
                if (t.Count > 0 && !IsComplete(t)) return false;
            return true;
        }

        private static void Shuffle(int[] arr, System.Random rng)
        {
            for (int i = arr.Length - 1; i > 0; i--)
            {
                int j = rng.Next(i + 1);
                (arr[i], arr[j]) = (arr[j], arr[i]);
            }
        }
    }
}

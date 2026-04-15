using System.Collections.Generic;
using UnityEngine;

namespace SuperGameApp.MiniGames.WaterSort
{
    /// <summary>
    /// Generates solvable Water Sort puzzle levels procedurally.
    /// Works by starting from a solved state and shuffling backwards.
    /// </summary>
    public static class LevelGenerator
    {
        /// <summary>
        /// Generate a random solvable level.
        /// </summary>
        /// <param name="colorCount">Number of distinct colors (= filled tubes)</param>
        /// <param name="emptyTubes">Number of extra empty tubes</param>
        /// <param name="layersPerTube">Layers per tube (typically 4)</param>
        /// <param name="shuffleMoves">Number of random moves to shuffle (higher = harder)</param>
        public static WaterSortLevel Generate(int levelNumber, int colorCount, int emptyTubes, int layersPerTube, int shuffleMoves)
        {
            int totalTubes = colorCount + emptyTubes;

            // Start with solved state: each tube has one color
            var tubes = new List<List<int>>();
            for (int c = 0; c < colorCount; c++)
            {
                var tube = new List<int>();
                for (int l = 0; l < layersPerTube; l++)
                    tube.Add(c + 1); // Color indices start at 1
                tubes.Add(tube);
            }
            // Add empty tubes
            for (int e = 0; e < emptyTubes; e++)
                tubes.Add(new List<int>());

            // Shuffle by performing random valid reverse-moves
            for (int i = 0; i < shuffleMoves; i++)
            {
                var validMoves = GetValidMoves(tubes, layersPerTube);
                if (validMoves.Count == 0) break;

                var move = validMoves[Random.Range(0, validMoves.Count)];
                PerformMove(tubes, move.from, move.to, layersPerTube);
            }

            // Convert to level data
            var level = new WaterSortLevel
            {
                LevelNumber = levelNumber,
                TubeCount = totalTubes,
                EmptyTubes = emptyTubes,
                ColorsCount = colorCount,
                LayersPerTube = layersPerTube,
                TubeData = FlattenTubes(tubes, layersPerTube)
            };

            return level;
        }

        /// <summary>
        /// Get difficulty parameters based on level number.
        /// </summary>
        public static (int colors, int empties, int shuffles) GetDifficultyForLevel(int level)
        {
            if (level <= 5)   return (3, 2, 20);
            if (level <= 15)  return (4, 2, 40);
            if (level <= 30)  return (5, 2, 60);
            if (level <= 50)  return (6, 2, 80);
            if (level <= 75)  return (7, 2, 100);
            if (level <= 100) return (8, 2, 120);
            return (9, 2, 150);
        }

        private static List<(int from, int to)> GetValidMoves(List<List<int>> tubes, int maxLayers)
        {
            var moves = new List<(int, int)>();

            for (int from = 0; from < tubes.Count; from++)
            {
                if (tubes[from].Count == 0) continue;

                int topColor = tubes[from][tubes[from].Count - 1];

                for (int to = 0; to < tubes.Count; to++)
                {
                    if (from == to) continue;
                    if (tubes[to].Count >= maxLayers) continue;

                    // Can pour if target is empty or top matches
                    if (tubes[to].Count == 0 || tubes[to][tubes[to].Count - 1] == topColor)
                    {
                        moves.Add((from, to));
                    }
                }
            }

            return moves;
        }

        private static void PerformMove(List<List<int>> tubes, int from, int to, int maxLayers)
        {
            if (tubes[from].Count == 0) return;
            if (tubes[to].Count >= maxLayers) return;

            int topColor = tubes[from][tubes[from].Count - 1];

            // Pour all matching top layers
            while (tubes[from].Count > 0 &&
                   tubes[to].Count < maxLayers &&
                   tubes[from][tubes[from].Count - 1] == topColor)
            {
                tubes[from].RemoveAt(tubes[from].Count - 1);
                tubes[to].Add(topColor);
            }
        }

        private static int[] FlattenTubes(List<List<int>> tubes, int layersPerTube)
        {
            var data = new int[tubes.Count * layersPerTube];
            for (int t = 0; t < tubes.Count; t++)
            {
                for (int l = 0; l < layersPerTube; l++)
                {
                    int idx = t * layersPerTube + l;
                    data[idx] = l < tubes[t].Count ? tubes[t][l] : 0;
                }
            }
            return data;
        }
    }
}

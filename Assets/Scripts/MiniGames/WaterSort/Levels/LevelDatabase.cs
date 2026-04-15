using System;
using System.Collections.Generic;
using UnityEngine;

namespace SuperGameApp.MiniGames.WaterSort
{
    /// <summary>
    /// ScriptableObject database holding all Water Sort levels.
    /// Create via Assets > Create > SuperGameApp > WaterSort > LevelDatabase
    /// </summary>
    [CreateAssetMenu(fileName = "WaterSortLevels", menuName = "SuperGameApp/WaterSort/LevelDatabase")]
    public class LevelDatabase : ScriptableObject
    {
        public List<WaterSortLevel> Levels = new List<WaterSortLevel>();
    }

    [Serializable]
    public class WaterSortLevel
    {
        public int LevelNumber;
        public int TubeCount;        // Total tubes including empty ones
        public int EmptyTubes;       // Number of empty tubes
        public int ColorsCount;      // Number of distinct colors
        public int LayersPerTube;    // Liquid layers per tube (usually 4)
        public int[] TubeData;       // Flattened tube contents: tube0layer0, tube0layer1, ..., tube1layer0, ...
                                     // 0 = empty, 1-N = color index

        /// <summary>
        /// Parses TubeData into a 2D array: [tubeIndex][layerIndex]
        /// Layer 0 = bottom, Layer N = top
        /// </summary>
        public int[,] GetTubeGrid()
        {
            int filledTubes = TubeCount;
            var grid = new int[filledTubes, LayersPerTube];

            for (int t = 0; t < filledTubes; t++)
            {
                for (int l = 0; l < LayersPerTube; l++)
                {
                    int idx = t * LayersPerTube + l;
                    grid[t, l] = idx < TubeData.Length ? TubeData[idx] : 0;
                }
            }

            return grid;
        }
    }
}

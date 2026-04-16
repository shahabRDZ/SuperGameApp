using System;
using System.Collections.Generic;
using UnityEngine;

namespace WaterSort.Core
{
    [Serializable]
    public class GameData
    {
        public int CurrentLevel = 1;
        public int Coins = 100;
        public int UndoCount = 5;
        public int HintCount = 4;
        public int AddTubeCount = 4;
        public List<LevelStar> Stars = new List<LevelStar>();

        public int GetStars(int level)
        {
            var s = Stars.Find(x => x.Level == level);
            return s != null ? s.StarCount : 0;
        }

        public void SetStars(int level, int stars)
        {
            var s = Stars.Find(x => x.Level == level);
            if (s != null) { if (stars > s.StarCount) s.StarCount = stars; }
            else Stars.Add(new LevelStar { Level = level, StarCount = stars });
        }
    }

    [Serializable]
    public class LevelStar
    {
        public int Level;
        public int StarCount;
    }

    public static class SaveSystem
    {
        private const string KEY = "WaterSortSave";

        public static void Save(GameData data)
        {
            PlayerPrefs.SetString(KEY, JsonUtility.ToJson(data));
            PlayerPrefs.Save();
        }

        public static GameData Load()
        {
            if (PlayerPrefs.HasKey(KEY))
                return JsonUtility.FromJson<GameData>(PlayerPrefs.GetString(KEY));
            return new GameData();
        }
    }
}

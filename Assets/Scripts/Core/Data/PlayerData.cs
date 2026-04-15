using System;
using System.Collections.Generic;
using UnityEngine;

namespace SuperGameApp.Core.Data
{
    /// <summary>
    /// Serializable player data for save/load system.
    /// </summary>
    [Serializable]
    public class PlayerData
    {
        public string Username;
        public int AvatarIndex;
        public int Coins;
        public int Gems;
        public int TotalScore;
        public int DailyRewardDay;
        public string LastDailyRewardDate;
        public bool AdsRemoved;

        // Per-game progress: gameId -> GameProgress
        public List<GameProgress> GameProgressList = new List<GameProgress>();

        // Settings
        public float MusicVolume = 1f;
        public float SfxVolume = 1f;
        public bool IsDarkTheme;
        public string Language = "en";

        public PlayerData()
        {
            Username = "Player";
            AvatarIndex = 0;
            Coins = 100;
            Gems = 5;
            TotalScore = 0;
            DailyRewardDay = 0;
            AdsRemoved = false;
        }

        public GameProgress GetGameProgress(string gameId)
        {
            var progress = GameProgressList.Find(g => g.GameId == gameId);
            if (progress == null)
            {
                progress = new GameProgress { GameId = gameId };
                GameProgressList.Add(progress);
            }
            return progress;
        }
    }

    [Serializable]
    public class GameProgress
    {
        public string GameId;
        public int HighestLevel;
        public int TotalStars;
        public int HighScore;
        public List<LevelResult> LevelResults = new List<LevelResult>();
    }

    [Serializable]
    public class LevelResult
    {
        public int LevelNumber;
        public int Stars;       // 1-3
        public int Score;
        public float BestTime;
    }
}

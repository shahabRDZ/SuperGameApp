using System;
using System.Collections.Generic;
using UnityEngine;

namespace SuperGameApp.Core.Data
{
    /// <summary>
    /// ScriptableObject holding all mini-game metadata for the main menu.
    /// Create via Assets > Create > SuperGameApp > GameConfig
    /// </summary>
    [CreateAssetMenu(fileName = "GameConfig", menuName = "SuperGameApp/GameConfig")]
    public class GameConfig : ScriptableObject
    {
        public List<MiniGameInfo> MiniGames = new List<MiniGameInfo>();
        public DailyRewardConfig DailyRewards;
        public AdsConfig Ads;
    }

    [Serializable]
    public class MiniGameInfo
    {
        public string GameId;
        public string DisplayName;
        public string Description;
        public Sprite Icon;
        public Sprite Banner;
        public string SceneName;
        public bool IsLocked;
        public int UnlockCost;       // 0 = free
        public Color ThemeColor;
    }

    [Serializable]
    public class DailyRewardConfig
    {
        public int[] CoinRewards = { 50, 75, 100, 150, 200, 300, 500 };
        public int[] GemRewards =  { 0,  0,  1,   0,   2,   0,   5  };
    }

    [Serializable]
    public class AdsConfig
    {
        public int InterstitialFrequency = 3;  // Show every N levels
        public int RewardedAdCoinBonus = 50;
        public string AdMobAppId = "";
        public string BannerAdUnitId = "";
        public string InterstitialAdUnitId = "";
        public string RewardedAdUnitId = "";
    }
}

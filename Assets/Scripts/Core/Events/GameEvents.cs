using System;

namespace SuperGameApp.Core.Events
{
    /// <summary>
    /// Central event bus for decoupled communication between systems.
    /// </summary>
    public static class GameEvents
    {
        // Currency
        public static event Action<int> OnCoinsChanged;
        public static event Action<int> OnGemsChanged;

        // Game flow
        public static event Action<string> OnMiniGameSelected;
        public static event Action<int> OnLevelCompleted;
        public static event Action OnLevelFailed;
        public static event Action OnLevelRestarted;

        // UI
        public static event Action OnSettingsChanged;
        public static event Action<string> OnAchievementUnlocked;
        public static event Action OnDailyRewardClaimed;

        // Ads
        public static event Action OnRewardedAdCompleted;
        public static event Action OnInterstitialAdClosed;

        public static void FireCoinsChanged(int newAmount) => OnCoinsChanged?.Invoke(newAmount);
        public static void FireGemsChanged(int newAmount) => OnGemsChanged?.Invoke(newAmount);
        public static void FireMiniGameSelected(string gameId) => OnMiniGameSelected?.Invoke(gameId);
        public static void FireLevelCompleted(int stars) => OnLevelCompleted?.Invoke(stars);
        public static void FireLevelFailed() => OnLevelFailed?.Invoke();
        public static void FireLevelRestarted() => OnLevelRestarted?.Invoke();
        public static void FireSettingsChanged() => OnSettingsChanged?.Invoke();
        public static void FireAchievementUnlocked(string id) => OnAchievementUnlocked?.Invoke(id);
        public static void FireDailyRewardClaimed() => OnDailyRewardClaimed?.Invoke();
        public static void FireRewardedAdCompleted() => OnRewardedAdCompleted?.Invoke();
        public static void FireInterstitialAdClosed() => OnInterstitialAdClosed?.Invoke();
    }
}

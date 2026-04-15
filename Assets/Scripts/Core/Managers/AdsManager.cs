using System;
using UnityEngine;
using SuperGameApp.Core.Events;
using SuperGameApp.Core.Utils;

namespace SuperGameApp.Core.Managers
{
    /// <summary>
    /// Manages ad integration. Uses Unity Ads as primary SDK.
    /// Replace placeholder calls with actual SDK methods after importing Unity Ads package.
    /// </summary>
    public class AdsManager : Singleton<AdsManager>
    {
        private Action _onRewardedComplete;

        public void Initialize()
        {
            // TODO: Initialize Unity Ads / AdMob SDK
            // Advertisement.Initialize(gameId, testMode);
            Debug.Log("[AdsManager] Initialized");
        }

        public void ShowInterstitial()
        {
            if (SaveManager.Instance.Data.AdsRemoved) return;

            // TODO: Show interstitial ad
            // Advertisement.Show(interstitialPlacementId);
            Debug.Log("[AdsManager] Showing interstitial ad");
            GameEvents.FireInterstitialAdClosed();
        }

        public void ShowRewarded(Action onComplete)
        {
            _onRewardedComplete = onComplete;

            // TODO: Show rewarded ad
            // Advertisement.Show(rewardedPlacementId, new ShowOptions { resultCallback = HandleRewardedResult });
            Debug.Log("[AdsManager] Showing rewarded ad");

            // Simulate reward for development
            OnRewardedAdSuccess();
        }

        private void OnRewardedAdSuccess()
        {
            _onRewardedComplete?.Invoke();
            _onRewardedComplete = null;
            GameEvents.FireRewardedAdCompleted();
        }

        public void RemoveAds()
        {
            SaveManager.Instance.Data.AdsRemoved = true;
            SaveManager.Instance.Save();
        }
    }
}

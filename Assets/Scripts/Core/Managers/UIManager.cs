using System.Collections;
using UnityEngine;
using SuperGameApp.Core.Utils;

namespace SuperGameApp.Core.Managers
{
    /// <summary>
    /// Manages UI panels, transitions, and popup overlays.
    /// </summary>
    public class UIManager : Singleton<UIManager>
    {
        [SerializeField] private CanvasGroup _fadeOverlay;
        [SerializeField] private float _fadeDuration = 0.3f;

        public void ShowPanel(GameObject panel)
        {
            panel.SetActive(true);
            var canvasGroup = panel.GetComponent<CanvasGroup>();
            if (canvasGroup != null)
                StartCoroutine(FadeIn(canvasGroup));
        }

        public void HidePanel(GameObject panel)
        {
            var canvasGroup = panel.GetComponent<CanvasGroup>();
            if (canvasGroup != null)
                StartCoroutine(FadeOutAndDisable(canvasGroup, panel));
            else
                panel.SetActive(false);
        }

        public IEnumerator FadeIn(CanvasGroup group)
        {
            group.alpha = 0;
            float elapsed = 0;
            while (elapsed < _fadeDuration)
            {
                elapsed += Time.deltaTime;
                group.alpha = elapsed / _fadeDuration;
                yield return null;
            }
            group.alpha = 1;
        }

        public IEnumerator FadeOut(CanvasGroup group)
        {
            float elapsed = 0;
            while (elapsed < _fadeDuration)
            {
                elapsed += Time.deltaTime;
                group.alpha = 1 - (elapsed / _fadeDuration);
                yield return null;
            }
            group.alpha = 0;
        }

        private IEnumerator FadeOutAndDisable(CanvasGroup group, GameObject panel)
        {
            yield return FadeOut(group);
            panel.SetActive(false);
        }

        public IEnumerator TransitionToScene(string sceneName)
        {
            if (_fadeOverlay != null)
            {
                yield return FadeIn(_fadeOverlay);
                UnityEngine.SceneManagement.SceneManager.LoadScene(sceneName);
                yield return FadeOut(_fadeOverlay);
            }
            else
            {
                UnityEngine.SceneManagement.SceneManager.LoadScene(sceneName);
            }
        }
    }
}

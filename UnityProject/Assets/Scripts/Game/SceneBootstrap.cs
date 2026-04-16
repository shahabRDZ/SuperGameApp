using UnityEngine;
// Input handled via OnMouseDown on Bottle colliders

namespace WaterSort.Game
{
    /// <summary>
    /// Bootstraps the game scene by creating all necessary objects at runtime.
    /// Attach to an empty GameObject in the scene.
    /// </summary>
    public class SceneBootstrap : MonoBehaviour
    {
        private void Start()
        {
            // Camera
            var cam = Camera.main;
            if (cam == null)
            {
                var camObj = new GameObject("MainCamera");
                cam = camObj.AddComponent<Camera>();
                camObj.tag = "MainCamera";
            }
            cam.orthographic = true;
            cam.orthographicSize = 6f;
            cam.backgroundColor = new Color32(8, 10, 30, 255);
            cam.clearFlags = CameraClearFlags.SolidColor;
            cam.transform.position = new Vector3(0, 0, -10);

            // No EventSystem needed — using OnMouseDown on colliders

            // Create bottle prefab
            var bottlePrefab = BottleSetup.CreateBottlePrefab();
            bottlePrefab.SetActive(false);

            // Bottle container
            var container = new GameObject("BottleContainer");
            container.transform.position = new Vector3(0, 1.5f, 0);

            // Audio
            var audioObj = new GameObject("Audio");
            var audioSource = audioObj.AddComponent<AudioSource>();
            audioSource.playOnAwake = false;

            // Pour animator
            var pourObj = new GameObject("PourAnimator");
            var pourAnim = pourObj.AddComponent<PourAnimator>();

            // Game Manager
            var gmObj = new GameObject("GameManager");
            var gm = gmObj.AddComponent<GameManager>();

            // Set references via reflection
            var gmType = typeof(GameManager);
            var flags = System.Reflection.BindingFlags.NonPublic | System.Reflection.BindingFlags.Instance;
            gmType.GetField("bottlePrefab", flags)?.SetValue(gm, bottlePrefab);
            gmType.GetField("bottleContainer", flags)?.SetValue(gm, container.transform);
            gmType.GetField("pourAnimator", flags)?.SetValue(gm, pourAnim);
            gmType.GetField("sfxSource", flags)?.SetValue(gm, audioSource);

            // Create simple UI
            CreateUI();

            Debug.Log("[WaterSort] Scene bootstrapped. Game ready!");
        }

        private void CreateUI()
        {
            // For now, use OnGUI as a simple overlay
            // In production, you'd build this with Unity UI (Canvas + TMP)
            gameObject.AddComponent<SimpleGUI>();
        }
    }

    /// <summary>
    /// Temporary IMGUI overlay until proper Canvas UI is built.
    /// </summary>
    public class SimpleGUI : MonoBehaviour
    {
        private GUIStyle _labelStyle;
        private GUIStyle _buttonStyle;
        private GUIStyle _titleStyle;

        private void OnGUI()
        {
            if (_labelStyle == null)
            {
                _labelStyle = new GUIStyle(GUI.skin.label)
                {
                    fontSize = 18,
                    fontStyle = FontStyle.Bold,
                    alignment = TextAnchor.MiddleCenter
                };
                _labelStyle.normal.textColor = Color.white;

                _buttonStyle = new GUIStyle(GUI.skin.button)
                {
                    fontSize = 14,
                    fontStyle = FontStyle.Bold
                };

                _titleStyle = new GUIStyle(GUI.skin.label)
                {
                    fontSize = 24,
                    fontStyle = FontStyle.Bold,
                    alignment = TextAnchor.MiddleCenter
                };
                _titleStyle.normal.textColor = Color.white;
            }

            var gm = GameManager.Instance;
            if (gm == null) return;

            float sw = Screen.width;
            float sh = Screen.height;

            // Top bar
            GUI.Label(new Rect(sw/2 - 80, 10, 160, 30),
                      $"Level {gm.CurrentLevel}", _titleStyle);

            string diff = WaterSort.Core.LevelGenerator.GetDifficultyName(gm.CurrentLevel);
            GUI.Label(new Rect(sw/2 - 50, 40, 100, 20), diff, _labelStyle);

            GUI.Label(new Rect(10, 10, 100, 25), $"Moves: {gm.Moves}", _labelStyle);
            GUI.Label(new Rect(sw - 110, 10, 100, 25), $"Coins: {gm.Data?.Coins ?? 0}", _labelStyle);

            // Bottom buttons
            float btnW = 80, btnH = 40, gap = 10;
            float totalW = btnW * 3 + gap * 2;
            float startX = (sw - totalW) / 2;
            float btnY = sh - 60;

            if (GUI.Button(new Rect(startX, btnY, btnW, btnH),
                           $"Undo ({gm.Data?.UndoCount ?? 0})", _buttonStyle))
                gm.Undo();

            if (GUI.Button(new Rect(startX + btnW + gap, btnY, btnW, btnH),
                           $"Hint ({gm.Data?.HintCount ?? 0})", _buttonStyle))
                gm.GetHint();

            if (GUI.Button(new Rect(startX + (btnW + gap) * 2, btnY, btnW, btnH),
                           $"Add ({gm.Data?.AddTubeCount ?? 0})", _buttonStyle))
                gm.AddExtraTube();

            // Restart
            if (GUI.Button(new Rect(10, sh - 60, 70, 35), "Restart", _buttonStyle))
                gm.Restart();
        }
    }
}

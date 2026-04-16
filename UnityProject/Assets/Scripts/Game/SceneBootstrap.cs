using UnityEngine;

namespace WaterSort.Game
{
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
            cam.backgroundColor = new Color32(6, 8, 24, 255);
            cam.clearFlags = CameraClearFlags.SolidColor;
            cam.transform.position = new Vector3(0, 0, -10);

            // Background with stars
            CreateBackground();

            // Create bottle prefab
            var bottlePrefab = BottleSetup.CreateBottlePrefab();
            bottlePrefab.SetActive(false);

            // Bottle container
            var container = new GameObject("BottleContainer");
            container.transform.position = new Vector3(0, 1.2f, 0);

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

            // Set references
            var flags = System.Reflection.BindingFlags.NonPublic | System.Reflection.BindingFlags.Instance;
            var gmType = typeof(GameManager);
            gmType.GetField("bottlePrefab", flags)?.SetValue(gm, bottlePrefab);
            gmType.GetField("bottleContainer", flags)?.SetValue(gm, container.transform);
            gmType.GetField("pourAnimator", flags)?.SetValue(gm, pourAnim);
            gmType.GetField("sfxSource", flags)?.SetValue(gm, audioSource);

            // UI
            gameObject.AddComponent<SimpleGUI>();

            // Start!
            gm.LoadLevel(Mathf.Max(1, gm.Data.CurrentLevel));

            Debug.Log("[WaterSort] Game ready!");
        }

        private void CreateBackground()
        {
            // Dark gradient background quad
            int w = 256, h = 512;
            var tex = new Texture2D(w, h);
            tex.filterMode = FilterMode.Bilinear;

            var pixels = new Color[w * h];
            var rng = new System.Random(42);

            for (int y = 0; y < h; y++)
            {
                float t = y / (float)h;
                // Dark navy gradient
                float r = Mathf.Lerp(0.02f, 0.035f, t);
                float g = Mathf.Lerp(0.025f, 0.04f, t);
                float b = Mathf.Lerp(0.09f, 0.16f, t);

                for (int x = 0; x < w; x++)
                    pixels[y * w + x] = new Color(r, g, b, 1);
            }

            // Stars
            for (int i = 0; i < 120; i++)
            {
                int sx = rng.Next(w), sy = rng.Next(h);
                float brightness = 0.15f + (float)rng.NextDouble() * 0.4f;
                int sz = rng.Next(1, 3);
                for (int dx = -sz; dx <= sz; dx++)
                    for (int dy = -sz; dy <= sz; dy++)
                    {
                        int px = sx + dx, py = sy + dy;
                        if (px >= 0 && px < w && py >= 0 && py < h)
                        {
                            float d = Mathf.Sqrt(dx * dx + dy * dy);
                            float a = brightness * Mathf.Max(0, 1f - d / sz);
                            var old = pixels[py * w + px];
                            pixels[py * w + px] = new Color(
                                Mathf.Min(1, old.r + a * 0.8f),
                                Mathf.Min(1, old.g + a * 0.85f),
                                Mathf.Min(1, old.b + a),
                                1);
                        }
                    }
            }

            // Nebula glow
            for (int x = 0; x < w; x++)
                for (int y = 0; y < h; y++)
                {
                    float dx = (x - w * 0.5f) / w;
                    float dy = (y - h * 0.6f) / h;
                    float d = Mathf.Sqrt(dx * dx + dy * dy);
                    float glow = Mathf.Exp(-d * d / 0.08f) * 0.06f;
                    var old = pixels[y * w + x];
                    pixels[y * w + x] = new Color(
                        Mathf.Min(1, old.r + glow * 0.6f),
                        old.g,
                        Mathf.Min(1, old.b + glow),
                        1);
                }

            tex.SetPixels(pixels);
            tex.Apply();

            var bgObj = new GameObject("Background");
            bgObj.transform.position = new Vector3(0, 0, 5);
            var sr = bgObj.AddComponent<SpriteRenderer>();
            sr.sprite = Sprite.Create(tex, new Rect(0, 0, w, h), new Vector2(0.5f, 0.5f), 20);
            sr.sortingOrder = -100;
            bgObj.transform.localScale = new Vector3(1.5f, 1.5f, 1);
        }
    }

    public class SimpleGUI : MonoBehaviour
    {
        GUIStyle _lbl, _btn, _title, _diff, _box;
        Texture2D _btnTex, _btnHoverTex, _boxTex;
        bool _inited;

        void InitStyles()
        {
            if (_inited) return;
            _inited = true;

            _btnTex = MakeTex(2, 2, new Color32(30, 40, 80, 220));
            _btnHoverTex = MakeTex(2, 2, new Color32(50, 65, 120, 230));
            _boxTex = MakeTex(2, 2, new Color32(15, 20, 50, 200));

            _title = new GUIStyle(GUI.skin.label)
            {
                fontSize = 22, fontStyle = FontStyle.Bold,
                alignment = TextAnchor.MiddleCenter
            };
            _title.normal.textColor = Color.white;

            _lbl = new GUIStyle(GUI.skin.label)
            {
                fontSize = 15, fontStyle = FontStyle.Bold,
                alignment = TextAnchor.MiddleCenter
            };
            _lbl.normal.textColor = new Color(0.85f, 0.87f, 0.95f);

            _diff = new GUIStyle(GUI.skin.label)
            {
                fontSize = 11, fontStyle = FontStyle.Bold,
                alignment = TextAnchor.MiddleCenter
            };

            _btn = new GUIStyle(GUI.skin.button)
            {
                fontSize = 13, fontStyle = FontStyle.Bold,
                alignment = TextAnchor.MiddleCenter
            };
            _btn.normal.background = _btnTex;
            _btn.hover.background = _btnHoverTex;
            _btn.active.background = _btnHoverTex;
            _btn.normal.textColor = Color.white;
            _btn.hover.textColor = Color.white;
            _btn.border = new RectOffset(4, 4, 4, 4);
            _btn.padding = new RectOffset(8, 8, 6, 6);

            _box = new GUIStyle(GUI.skin.box);
            _box.normal.background = _boxTex;
        }

        Texture2D MakeTex(int w, int h, Color c)
        {
            var t = new Texture2D(w, h);
            for (int x = 0; x < w; x++)
                for (int y = 0; y < h; y++)
                    t.SetPixel(x, y, c);
            t.Apply();
            return t;
        }

        void OnGUI()
        {
            InitStyles();

            var gm = GameManager.Instance;
            if (gm == null) return;

            float sw = Screen.width, sh = Screen.height;

            // ─── TOP BAR ───
            GUI.Box(new Rect(0, 0, sw, 65), "", _box);

            // Level badge (center)
            GUI.Label(new Rect(sw / 2 - 80, 8, 160, 28), $"Level {gm.CurrentLevel}", _title);

            // Difficulty
            string diff = WaterSort.Core.LevelGenerator.GetDifficultyName(gm.CurrentLevel);
            Color dc = WaterSort.Core.ColorPalette.GetDifficultyColor(diff);
            _diff.normal.textColor = dc;
            GUI.Label(new Rect(sw / 2 - 40, 34, 80, 18), diff, _diff);

            // Moves (left)
            _lbl.alignment = TextAnchor.MiddleLeft;
            GUI.Label(new Rect(12, 18, 120, 25), $"Moves: {gm.Moves}", _lbl);

            // Coins (right)
            _lbl.alignment = TextAnchor.MiddleRight;
            GUI.Label(new Rect(sw - 130, 18, 120, 25), $"Coins: {gm.Data?.Coins ?? 0}", _lbl);
            _lbl.alignment = TextAnchor.MiddleCenter;

            // ─── BOTTOM BUTTONS ───
            float btnW = 85, btnH = 38, gap = 8;
            float totalW = btnW * 4 + gap * 3;
            float startX = (sw - totalW) / 2;
            float btnY = sh - 55;

            // Button bar background
            GUI.Box(new Rect(startX - 12, btnY - 8, totalW + 24, btnH + 16), "", _box);

            if (GUI.Button(new Rect(startX, btnY, btnW, btnH),
                $"↩ Undo ({gm.Data?.UndoCount ?? 0})", _btn))
                gm.Undo();

            if (GUI.Button(new Rect(startX + btnW + gap, btnY, btnW, btnH),
                $"💡 Hint ({gm.Data?.HintCount ?? 0})", _btn))
                gm.GetHint();

            if (GUI.Button(new Rect(startX + (btnW + gap) * 2, btnY, btnW, btnH),
                $"+ Add ({gm.Data?.AddTubeCount ?? 0})", _btn))
                gm.AddExtraTube();

            if (GUI.Button(new Rect(startX + (btnW + gap) * 3, btnY, btnW, btnH),
                "↻ Restart", _btn))
                gm.Restart();
        }
    }
}

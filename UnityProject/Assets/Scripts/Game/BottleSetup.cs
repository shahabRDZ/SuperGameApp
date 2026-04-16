using UnityEngine;

namespace WaterSort.Game
{
    /// <summary>
    /// Auto-creates a bottle prefab at runtime with proper sprites and structure.
    /// Attach this to an empty GameObject to generate the bottle hierarchy.
    /// </summary>
    public class BottleSetup : MonoBehaviour
    {
        public static GameObject CreateBottlePrefab()
        {
            var root = new GameObject("Bottle");

            // Add Bottle component
            var bottle = root.AddComponent<Bottle>();

            // Add collider for clicks
            var col = root.AddComponent<BoxCollider2D>();
            col.size = new Vector2(0.8f, 2.8f);
            col.offset = new Vector2(0, -0.2f);

            // Body sprite
            var bodyObj = new GameObject("Body");
            bodyObj.transform.SetParent(root.transform);
            bodyObj.transform.localPosition = Vector3.zero;
            var bodyRenderer = bodyObj.AddComponent<SpriteRenderer>();
            bodyRenderer.sprite = CreateBottleSprite();
            bodyRenderer.sortingOrder = 0;

            // Glow
            var glowObj = new GameObject("Glow");
            glowObj.transform.SetParent(root.transform);
            glowObj.transform.localPosition = Vector3.zero;
            glowObj.transform.localScale = Vector3.one * 1.15f;
            var glowRenderer = glowObj.AddComponent<SpriteRenderer>();
            glowRenderer.sprite = CreateGlowSprite();
            glowRenderer.sortingOrder = -1;
            glowRenderer.enabled = false;

            // Liquid layers (4)
            var layerRenderers = new SpriteRenderer[4];
            for (int i = 0; i < 4; i++)
            {
                var layerObj = new GameObject($"Layer_{i}");
                layerObj.transform.SetParent(root.transform);
                layerObj.transform.localPosition = new Vector3(0, -0.85f + i * 0.45f, 0);
                var lr = layerObj.AddComponent<SpriteRenderer>();
                lr.sprite = CreateLayerSprite(i == 0);
                lr.sortingOrder = 1 + i;
                lr.enabled = false;
                layerRenderers[i] = lr;
            }

            // Complete badge
            var badgeObj = new GameObject("CompleteBadge");
            badgeObj.transform.SetParent(root.transform);
            badgeObj.transform.localPosition = new Vector3(0, 1.2f, 0);
            badgeObj.SetActive(false);
            var badgeRenderer = badgeObj.AddComponent<SpriteRenderer>();
            badgeRenderer.sprite = CreateBadgeSprite();
            badgeRenderer.sortingOrder = 10;

            // Particles
            var particleObj = new GameObject("Particles");
            particleObj.transform.SetParent(root.transform);
            particleObj.transform.localPosition = Vector3.zero;
            var ps = particleObj.AddComponent<ParticleSystem>();
            SetupParticles(ps);

            // Set references via reflection-free approach
            // The Bottle component will find children by name
            SetBottleReferences(bottle, layerRenderers, bodyRenderer, glowRenderer,
                               badgeObj, ps);

            return root;
        }

        private static void SetBottleReferences(Bottle bottle, SpriteRenderer[] layers,
            SpriteRenderer body, SpriteRenderer glow, GameObject badge, ParticleSystem ps)
        {
            // Use serialized field setter via SerializedObject in editor,
            // or for runtime: we use the Init method directly
            // The Bottle class fields are [SerializeField] so we set them via reflection
            var type = typeof(Bottle);
            var flags = System.Reflection.BindingFlags.NonPublic | System.Reflection.BindingFlags.Instance;

            type.GetField("layerRenderers", flags)?.SetValue(bottle, layers);
            type.GetField("bottleBody", flags)?.SetValue(bottle, body);
            type.GetField("glowRenderer", flags)?.SetValue(bottle, glow);
            type.GetField("completeBadge", flags)?.SetValue(bottle, badge);
            type.GetField("completeParticles", flags)?.SetValue(bottle, ps);
        }

        private static Sprite CreateBottleSprite()
        {
            int w = 64, h = 192;
            var tex = new Texture2D(w, h);
            tex.filterMode = FilterMode.Bilinear;

            Color clear = Color.clear;
            Color glass = new Color32(25, 35, 80, 220);
            Color highlight = new Color32(60, 80, 150, 180);
            Color rim = new Color32(50, 70, 140, 200);

            // Clear
            for (int x = 0; x < w; x++)
                for (int y = 0; y < h; y++)
                    tex.SetPixel(x, y, clear);

            // Body (rounded rect with bottom curve)
            int bodyLeft = 8, bodyRight = w - 8;
            int bodyTop = 48, bodyBottom = 20;
            int neckLeft = 20, neckRight = w - 20;
            int neckTop = 168, neckBottom = 150;
            int capLeft = 24, capRight = w - 24;
            int capTop = 184, capBottom = 170;

            // Draw body
            for (int x = bodyLeft; x < bodyRight; x++)
            {
                float t = (x - bodyLeft) / (float)(bodyRight - bodyLeft);
                float brightness = 0.3f + 0.7f * Mathf.Exp(-Mathf.Pow(t - 0.35f, 2) / 0.08f);

                Color col = Color.Lerp(new Color32(10, 15, 40, 220), highlight, brightness);

                for (int y = bodyBottom; y < bodyTop + 80; y++)
                {
                    // Bottom curve
                    if (y < bodyBottom + 16)
                    {
                        float dy = (bodyBottom + 16 - y) / 16f;
                        float dx = Mathf.Abs(t - 0.5f) * 2f;
                        if (dx * dx + dy * dy > 1f) continue;
                        col.a = 0.85f - dy * 0.2f;
                    }
                    tex.SetPixel(x, y, col);
                }
            }

            // Neck
            for (int x = neckLeft; x < neckRight; x++)
            {
                float t = (x - neckLeft) / (float)(neckRight - neckLeft);
                float brightness = 0.4f + 0.6f * Mathf.Exp(-Mathf.Pow(t - 0.3f, 2) / 0.1f);
                Color col = Color.Lerp(new Color32(15, 20, 50, 200), highlight, brightness);

                for (int y = neckBottom; y < neckTop; y++)
                    tex.SetPixel(x, y, col);
            }

            // Cap
            for (int x = capLeft; x < capRight; x++)
            {
                float t = (x - capLeft) / (float)(capRight - capLeft);
                float brightness = 0.5f + 0.5f * Mathf.Exp(-Mathf.Pow(t - 0.4f, 2) / 0.15f);
                Color col = Color.Lerp(new Color32(30, 45, 100, 230), rim, brightness);

                for (int y = capBottom; y < capTop; y++)
                    tex.SetPixel(x, y, col);
            }

            // Borders
            for (int y = bodyBottom + 16; y < bodyTop + 80; y++)
            {
                tex.SetPixel(bodyLeft, y, rim);
                tex.SetPixel(bodyLeft + 1, y, rim);
                tex.SetPixel(bodyRight - 1, y, new Color(rim.r, rim.g, rim.b, 0.6f));
                tex.SetPixel(bodyRight - 2, y, new Color(rim.r, rim.g, rim.b, 0.6f));
            }

            tex.Apply();
            return Sprite.Create(tex, new Rect(0, 0, w, h), new Vector2(0.5f, 0.5f), 64);
        }

        private static Sprite CreateLayerSprite(bool isBottom)
        {
            int w = 48, h = 28;
            var tex = new Texture2D(w, h);
            tex.filterMode = FilterMode.Bilinear;

            for (int x = 0; x < w; x++)
            {
                for (int y = 0; y < h; y++)
                {
                    float t = y / (float)h;
                    float alpha = 0.95f;

                    // Bottom curve for bottom layer
                    if (isBottom && y < 8)
                    {
                        float dy = (8 - y) / 8f;
                        float dx = Mathf.Abs((x - w / 2f) / (w / 2f));
                        if (dx * dx + dy * dy > 1f) { tex.SetPixel(x, y, Color.clear); continue; }
                    }

                    // Slight gradient
                    float brightness = 0.85f + 0.15f * t;
                    tex.SetPixel(x, y, new Color(brightness, brightness, brightness, alpha));
                }
            }

            tex.Apply();
            return Sprite.Create(tex, new Rect(0, 0, w, h), new Vector2(0.5f, 0.5f), 64);
        }

        private static Sprite CreateGlowSprite()
        {
            int sz = 80;
            var tex = new Texture2D(sz, sz * 3);
            tex.filterMode = FilterMode.Bilinear;

            for (int x = 0; x < sz; x++)
                for (int y = 0; y < sz * 3; y++)
                {
                    float dx = (x - sz / 2f) / (sz / 2f);
                    float dy = (y - sz * 1.5f) / (sz * 1.5f);
                    float d = Mathf.Sqrt(dx * dx + dy * dy);
                    float a = Mathf.Max(0, 1f - d) * 0.3f;
                    tex.SetPixel(x, y, new Color(1, 1, 1, a));
                }

            tex.Apply();
            return Sprite.Create(tex, new Rect(0, 0, sz, sz * 3), new Vector2(0.5f, 0.5f), 32);
        }

        private static Sprite CreateBadgeSprite()
        {
            int sz = 24;
            var tex = new Texture2D(sz, sz);
            tex.filterMode = FilterMode.Bilinear;

            for (int x = 0; x < sz; x++)
                for (int y = 0; y < sz; y++)
                {
                    float dx = (x - sz / 2f) / (sz / 2f);
                    float dy = (y - sz / 2f) / (sz / 2f);
                    if (dx * dx + dy * dy <= 1f)
                        tex.SetPixel(x, y, new Color32(76, 175, 80, 255));
                    else
                        tex.SetPixel(x, y, Color.clear);
                }

            tex.Apply();
            return Sprite.Create(tex, new Rect(0, 0, sz, sz), new Vector2(0.5f, 0.5f), 24);
        }

        private static void SetupParticles(ParticleSystem ps)
        {
            var main = ps.main;
            main.startLifetime = 0.8f;
            main.startSpeed = 3f;
            main.startSize = 0.15f;
            main.maxParticles = 50;
            main.simulationSpace = ParticleSystemSimulationSpace.World;
            main.playOnAwake = false;
            main.startColor = Color.white;
            main.gravityModifier = 0.5f;

            var emission = ps.emission;
            emission.rateOverTime = 0;
            emission.SetBursts(new[] { new ParticleSystem.Burst(0, 30) });

            var shape = ps.shape;
            shape.shapeType = ParticleSystemShapeType.Circle;
            shape.radius = 0.3f;

            var renderer = ps.GetComponent<ParticleSystemRenderer>();
            renderer.sortingOrder = 20;
        }
    }
}

using UnityEngine;
using System.Collections.Generic;

namespace WaterSort.Game
{
    /// <summary>
    /// Creates high-quality bottle prefab at runtime with 3D cylindrical shading.
    /// Matches commercial reference: metallic blue glass, cap, neck, body, base, glow.
    /// </summary>
    public static class BottleSetup
    {
        // Sprite resolution (high quality)
        const int TEX_W = 128;
        const int TEX_H = 384;
        const int LAYER_W = 100;
        const int LAYER_H = 64;
        const int GLOW_W = 160;
        const int GLOW_H = 440;
        const float PPU = 128f; // pixels per unit

        public static GameObject CreateBottlePrefab()
        {
            var root = new GameObject("Bottle");
            var bottle = root.AddComponent<Bottle>();

            // Collider
            var col = root.AddComponent<BoxCollider2D>();
            col.size = new Vector2(0.9f, 2.8f);
            col.offset = new Vector2(0, -0.1f);

            // === GLOW (behind everything) ===
            var glowObj = CreateChild(root, "Glow", 0, 0, -1);
            var glowR = glowObj.AddComponent<SpriteRenderer>();
            glowR.sprite = MakeGlowSprite();
            glowR.enabled = false;

            // === BODY ===
            var bodyObj = CreateChild(root, "Body", 0, 0, 0);
            var bodyR = bodyObj.AddComponent<SpriteRenderer>();
            bodyR.sprite = MakeBottleSprite();

            // === LIQUID LAYERS (4) ===
            var layers = new SpriteRenderer[4];
            float layerStartY = -0.95f;
            float layerStep = 0.5f;
            for (int i = 0; i < 4; i++)
            {
                var lObj = CreateChild(root, $"Layer{i}", 0, layerStartY + i * layerStep, 1 + i);
                var lr = lObj.AddComponent<SpriteRenderer>();
                lr.sprite = MakeLayerSprite(i == 0);
                lr.enabled = false;
                layers[i] = lr;
            }

            // === COMPLETE BADGE ===
            var badge = CreateChild(root, "CompleteBadge", 0, 1.35f, 10);
            var badgeR = badge.AddComponent<SpriteRenderer>();
            badgeR.sprite = MakeBadgeSprite();
            badge.SetActive(false);

            // === PARTICLES ===
            var pObj = CreateChild(root, "Particles", 0, 0, 20);
            var ps = pObj.AddComponent<ParticleSystem>();
            SetupParticles(ps);

            // Wire references
            SetField(bottle, "layerRenderers", layers);
            SetField(bottle, "bottleBody", bodyR);
            SetField(bottle, "glowRenderer", glowR);
            SetField(bottle, "completeBadge", badge);
            SetField(bottle, "completeParticles", ps);

            return root;
        }

        static GameObject CreateChild(GameObject parent, string name, float x, float y, int sortOrder)
        {
            var obj = new GameObject(name);
            obj.transform.SetParent(parent.transform);
            obj.transform.localPosition = new Vector3(x, y, 0);
            return obj;
        }

        static void SetField(object target, string name, object value)
        {
            var f = target.GetType().GetField(name,
                System.Reflection.BindingFlags.NonPublic | System.Reflection.BindingFlags.Instance);
            f?.SetValue(target, value);
        }

        // ═══════════════════════════════════════
        //  BOTTLE SPRITE — 3D metallic blue glass
        // ═══════════════════════════════════════

        static Sprite MakeBottleSprite()
        {
            var tex = new Texture2D(TEX_W, TEX_H);
            tex.filterMode = FilterMode.Bilinear;
            tex.wrapMode = TextureWrapMode.Clamp;

            var pixels = new Color[TEX_W * TEX_H];
            // Clear
            for (int i = 0; i < pixels.Length; i++) pixels[i] = Color.clear;

            // Bottle dimensions in pixels
            int bodyL = 14, bodyR = TEX_W - 14;
            int bodyBot = 30, bodyTop = 290;
            int neckL = 38, neckR = TEX_W - 38;
            int neckBot = 290, neckTop = 330;
            int capL = 42, capR = TEX_W - 42;
            int capBot = 330, capTop = 350;
            int baseBot = 8, baseTop = 30;
            int botCurve = 24; // bottom roundness

            // === BODY ===
            for (int x = bodyL; x < bodyR; x++)
            {
                float nx = (x - bodyL) / (float)(bodyR - bodyL); // 0-1
                float t = (nx - 0.5f) * 2f; // -1 to 1

                // Cylindrical shading
                float cyl = 0.25f + 0.75f * Mathf.Exp(-Mathf.Pow(t + 0.3f, 2) / 0.08f);

                // Base color: dark navy blue
                float br = Mathf.Clamp01(0.08f * cyl * 2.5f);
                float bg = Mathf.Clamp01(0.12f * cyl * 2.5f);
                float bb = Mathf.Clamp01(0.32f * cyl * 2.5f);

                for (int y = bodyBot; y < bodyTop; y++)
                {
                    // Bottom curve check
                    if (y < bodyBot + botCurve)
                    {
                        float dy = (float)(bodyBot + botCurve - y) / botCurve;
                        float dx = Mathf.Abs(t);
                        if (dx * dx + dy * dy > 1f) continue;
                        // Darken in curve
                        float darkFactor = 1f - dy * 0.3f;
                        pixels[y * TEX_W + x] = new Color(br * darkFactor, bg * darkFactor, bb * darkFactor, 0.92f);
                    }
                    else
                    {
                        pixels[y * TEX_W + x] = new Color(br, bg, bb, 0.92f);
                    }
                }
            }

            // === HIGHLIGHT STREAKS ===
            // Main left highlight
            for (int y = bodyBot + botCurve + 5; y < bodyTop - 5; y++)
            {
                float ny = (y - bodyBot - botCurve - 5f) / (bodyTop - bodyBot - botCurve - 10f);
                float intensity = Mathf.Exp(-Mathf.Pow(ny - 0.12f, 2) / 0.005f) * 0.45f
                                + Mathf.Exp(-Mathf.Pow(ny - 0.5f, 2) / 0.04f) * 0.2f;

                for (int dx = 0; dx < 10; dx++)
                {
                    int x = bodyL + 4 + dx;
                    float falloff = Mathf.Max(0, 1f - dx / 9f);
                    float a = intensity * falloff;
                    if (a > 0.01f && x < TEX_W)
                    {
                        var px = pixels[y * TEX_W + x];
                        pixels[y * TEX_W + x] = new Color(
                            Mathf.Min(1, px.r + a),
                            Mathf.Min(1, px.g + a),
                            Mathf.Min(1, px.b + a * 0.8f),
                            px.a);
                    }
                }
            }

            // Right subtle highlight
            for (int y = bodyBot + botCurve + 15; y < bodyTop - 15; y++)
            {
                float ny = (y - bodyBot - botCurve - 15f) / (bodyTop - bodyBot - botCurve - 30f);
                float intensity = Mathf.Exp(-Mathf.Pow(ny - 0.35f, 2) / 0.03f) * 0.12f;
                for (int dx = 0; dx < 5; dx++)
                {
                    int x = bodyR - 6 - dx;
                    float falloff = Mathf.Max(0, 1f - dx / 4f);
                    float a = intensity * falloff;
                    if (a > 0.01f && x >= 0)
                    {
                        var px = pixels[y * TEX_W + x];
                        pixels[y * TEX_W + x] = new Color(
                            Mathf.Min(1, px.r + a),
                            Mathf.Min(1, px.g + a),
                            Mathf.Min(1, px.b + a),
                            px.a);
                    }
                }
            }

            // === BORDER LINES ===
            Color borderC = new Color(0.2f, 0.28f, 0.55f, 0.75f);
            Color borderBright = new Color(0.3f, 0.4f, 0.65f, 0.65f);
            for (int y = bodyBot + botCurve; y < bodyTop; y++)
            {
                SetPx(pixels, bodyL, y, borderBright);
                SetPx(pixels, bodyL + 1, y, borderBright);
                SetPx(pixels, bodyR - 1, y, borderC);
                SetPx(pixels, bodyR - 2, y, borderC);
            }

            // Bottom arc border
            for (int angle = 0; angle <= 180; angle++)
            {
                float rad = angle * Mathf.Deg2Rad;
                int bx = (int)(bodyL + (bodyR - bodyL) / 2f + (bodyR - bodyL) / 2f * Mathf.Cos(rad));
                int by = (int)(bodyBot + botCurve - botCurve * Mathf.Sin(rad));
                if (bx >= 0 && bx < TEX_W && by >= 0 && by < TEX_H)
                    pixels[by * TEX_W + bx] = borderC;
            }

            // === NECK ===
            for (int x = neckL; x < neckR; x++)
            {
                float t = ((x - neckL) / (float)(neckR - neckL) - 0.5f) * 2f;
                float cyl = 0.35f + 0.65f * Mathf.Exp(-Mathf.Pow(t + 0.2f, 2) / 0.1f);
                float r = 0.07f * cyl * 2f;
                float g = 0.1f * cyl * 2f;
                float b = 0.28f * cyl * 2f;
                for (int y = neckBot; y < neckTop; y++)
                    pixels[y * TEX_W + x] = new Color(r, g, b, 0.88f);
            }
            // Neck borders
            for (int y = neckBot; y < neckTop; y++)
            {
                SetPx(pixels, neckL, y, borderC);
                SetPx(pixels, neckR - 1, y, borderC);
            }

            // Shoulder lines
            DrawLine(pixels, neckL, neckBot, bodyL + 2, bodyTop, borderC);
            DrawLine(pixels, neckR - 1, neckBot, bodyR - 2, bodyTop, borderC);

            // === CAP ===
            for (int x = capL; x < capR; x++)
            {
                float t = ((x - capL) / (float)(capR - capL) - 0.5f) * 2f;
                float cyl = 0.45f + 0.55f * Mathf.Exp(-Mathf.Pow(t, 2) / 0.15f);
                float r = 0.15f * cyl * 2f;
                float g = 0.2f * cyl * 2f;
                float b = 0.45f * cyl * 2f;
                for (int y = capBot; y < capTop; y++)
                    pixels[y * TEX_W + x] = new Color(r, g, b, 0.9f);
            }
            // Cap border
            for (int x = capL; x < capR; x++)
            {
                SetPx(pixels, x, capTop - 1, new Color(0.25f, 0.35f, 0.6f, 0.6f));
                SetPx(pixels, x, capBot, new Color(0.2f, 0.28f, 0.5f, 0.5f));
            }

            // === BASE/STAND ===
            int baseMid = (bodyL + bodyR) / 2;
            int baseHalfW = (bodyR - bodyL) / 2 + 4;
            for (int y = baseBot; y < baseTop; y++)
            {
                float ny = (y - baseBot) / (float)(baseTop - baseBot);
                float w = baseHalfW * (0.7f + 0.3f * (1f - ny)); // slightly trapezoidal
                for (int x = (int)(baseMid - w); x < (int)(baseMid + w); x++)
                {
                    if (x < 0 || x >= TEX_W) continue;
                    float t = Mathf.Abs((x - baseMid) / w);
                    float brightness = 0.5f + 0.3f * (1f - t) - 0.15f * ny;
                    pixels[y * TEX_W + x] = new Color(brightness * 0.85f, brightness * 0.8f, brightness * 0.7f, 0.7f);
                }
            }

            tex.SetPixels(pixels);
            tex.Apply();
            return Sprite.Create(tex, new Rect(0, 0, TEX_W, TEX_H), new Vector2(0.5f, 0.5f), PPU);
        }

        // ═══════════════════════════════════════
        //  LIQUID LAYER SPRITE
        // ═══════════════════════════════════════

        static Sprite MakeLayerSprite(bool isBottom)
        {
            var tex = new Texture2D(LAYER_W, LAYER_H);
            tex.filterMode = FilterMode.Bilinear;
            var pixels = new Color[LAYER_W * LAYER_H];

            int curveH = isBottom ? 18 : 0;

            for (int x = 0; x < LAYER_W; x++)
            {
                float nx = x / (float)LAYER_W;
                float t = (nx - 0.5f) * 2f; // -1 to 1

                // Cylindrical shading on liquid
                float cyl = 0.85f + 0.15f * Mathf.Exp(-Mathf.Pow(t + 0.25f, 2) / 0.08f);
                // Edge darkening
                float edge = 1f - Mathf.Pow(Mathf.Abs(t), 4) * 0.2f;

                for (int y = 0; y < LAYER_H; y++)
                {
                    // Bottom curve
                    if (isBottom && y < curveH)
                    {
                        float dy = (float)(curveH - y) / curveH;
                        float dx = Mathf.Abs(t);
                        if (dx * dx + dy * dy > 1f) { pixels[y * LAYER_W + x] = Color.clear; continue; }
                    }

                    float ny = y / (float)LAYER_H;
                    // Subtle gradient: slightly bright at top
                    float grad = 0.9f + 0.1f * ny;

                    float final_brightness = cyl * edge * grad;
                    pixels[y * LAYER_W + x] = new Color(final_brightness, final_brightness, final_brightness, 0.95f);
                }
            }

            // Left shine strip
            for (int y = 2; y < LAYER_H - 2; y++)
            {
                float ny = (y - 2f) / (LAYER_H - 4f);
                float a = Mathf.Sin(ny * Mathf.PI) * 0.25f;
                for (int dx = 0; dx < 6; dx++)
                {
                    float fa = a * (1f - dx / 5f);
                    if (fa > 0.01f)
                    {
                        var px = pixels[y * LAYER_W + 3 + dx];
                        pixels[y * LAYER_W + 3 + dx] = new Color(
                            Mathf.Min(1, px.r + fa),
                            Mathf.Min(1, px.g + fa),
                            Mathf.Min(1, px.b + fa),
                            px.a);
                    }
                }
            }

            tex.SetPixels(pixels);
            tex.Apply();
            return Sprite.Create(tex, new Rect(0, 0, LAYER_W, LAYER_H), new Vector2(0.5f, 0.5f), PPU);
        }

        // ═══════════════════════════════════════
        //  GLOW SPRITE
        // ═══════════════════════════════════════

        static Sprite MakeGlowSprite()
        {
            var tex = new Texture2D(GLOW_W, GLOW_H);
            tex.filterMode = FilterMode.Bilinear;
            var pixels = new Color[GLOW_W * GLOW_H];

            float cx = GLOW_W / 2f, cy = GLOW_H / 2f;

            for (int x = 0; x < GLOW_W; x++)
            {
                for (int y = 0; y < GLOW_H; y++)
                {
                    float dx = (x - cx) / cx;
                    float dy = (y - cy) / cy;
                    float d = Mathf.Sqrt(dx * dx * 1.5f + dy * dy);

                    // Soft glow falloff
                    float a = Mathf.Max(0, 1f - d) * 0.4f;
                    // Stronger at edges (ring-like)
                    float ring = Mathf.Exp(-Mathf.Pow(d - 0.7f, 2) / 0.05f) * 0.3f;

                    pixels[y * GLOW_W + x] = new Color(1, 1, 1, Mathf.Min(0.6f, a + ring));
                }
            }

            tex.SetPixels(pixels);
            tex.Apply();
            return Sprite.Create(tex, new Rect(0, 0, GLOW_W, GLOW_H), new Vector2(0.5f, 0.5f), PPU * 0.9f);
        }

        // ═══════════════════════════════════════
        //  BADGE SPRITE
        // ═══════════════════════════════════════

        static Sprite MakeBadgeSprite()
        {
            int sz = 32;
            var tex = new Texture2D(sz, sz);
            tex.filterMode = FilterMode.Bilinear;
            var pixels = new Color[sz * sz];

            float c = sz / 2f;
            for (int x = 0; x < sz; x++)
                for (int y = 0; y < sz; y++)
                {
                    float d = Mathf.Sqrt((x - c) * (x - c) + (y - c) * (y - c));
                    if (d < c - 1)
                    {
                        float t = d / c;
                        // Green with slight gradient
                        pixels[y * sz + x] = new Color(0.3f + 0.1f * (1 - t), 0.75f + 0.1f * (1 - t), 0.35f, 1);
                    }
                    else if (d < c)
                        pixels[y * sz + x] = new Color(0.45f, 0.85f, 0.5f, 0.8f); // edge
                    else
                        pixels[y * sz + x] = Color.clear;
                }

            // Checkmark (simple lines)
            DrawLine(pixels, sz, 9, 15, 13, 19, Color.white);
            DrawLine(pixels, sz, 13, 19, 22, 10, Color.white);
            DrawLine(pixels, sz, 9, 14, 13, 18, Color.white);
            DrawLine(pixels, sz, 13, 18, 22, 9, Color.white);

            tex.SetPixels(pixels);
            tex.Apply();
            return Sprite.Create(tex, new Rect(0, 0, sz, sz), new Vector2(0.5f, 0.5f), 32);
        }

        // ═══════════════════════════════════════
        //  PARTICLES
        // ═══════════════════════════════════════

        static void SetupParticles(ParticleSystem ps)
        {
            var main = ps.main;
            main.startLifetime = 1f;
            main.startSpeed = new ParticleSystem.MinMaxCurve(2f, 5f);
            main.startSize = new ParticleSystem.MinMaxCurve(0.08f, 0.2f);
            main.maxParticles = 60;
            main.simulationSpace = ParticleSystemSimulationSpace.World;
            main.playOnAwake = false;
            main.gravityModifier = 0.4f;

            var emission = ps.emission;
            emission.rateOverTime = 0;
            emission.SetBursts(new[] { new ParticleSystem.Burst(0, 35) });

            var shape = ps.shape;
            shape.shapeType = ParticleSystemShapeType.Circle;
            shape.radius = 0.4f;

            var col = ps.colorOverLifetime;
            col.enabled = true;
            var gradient = new Gradient();
            gradient.SetKeys(
                new[] { new GradientColorKey(Color.white, 0), new GradientColorKey(Color.white, 1) },
                new[] { new GradientAlphaKey(1, 0), new GradientAlphaKey(0, 1) }
            );
            col.color = gradient;

            var renderer = ps.GetComponent<ParticleSystemRenderer>();
            renderer.sortingOrder = 20;
        }

        // ═══════════════════════════════════════
        //  HELPERS
        // ═══════════════════════════════════════

        static void SetPx(Color[] pixels, int x, int y, Color c)
        {
            if (x >= 0 && x < TEX_W && y >= 0 && y < TEX_H)
                pixels[y * TEX_W + x] = c;
        }

        static void DrawLine(Color[] pixels, int x0, int y0, int x1, int y1, Color c)
        {
            DrawLine(pixels, TEX_W, x0, y0, x1, y1, c);
        }

        static void DrawLine(Color[] pixels, int w, int x0, int y0, int x1, int y1, Color c)
        {
            int dx = Mathf.Abs(x1 - x0), dy = Mathf.Abs(y1 - y0);
            int sx = x0 < x1 ? 1 : -1, sy = y0 < y1 ? 1 : -1;
            int err = dx - dy;
            int maxW = w;
            int maxH = pixels.Length / w;

            while (true)
            {
                if (x0 >= 0 && x0 < maxW && y0 >= 0 && y0 < maxH)
                    pixels[y0 * w + x0] = c;
                if (x0 == x1 && y0 == y1) break;
                int e2 = 2 * err;
                if (e2 > -dy) { err -= dy; x0 += sx; }
                if (e2 < dx) { err += dx; y0 += sy; }
            }
        }
    }
}

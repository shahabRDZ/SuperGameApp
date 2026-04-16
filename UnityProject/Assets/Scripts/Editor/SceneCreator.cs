#if UNITY_EDITOR
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;

namespace WaterSort.EditorTools
{
    public static class SceneCreator
    {
        [MenuItem("WaterSort/Create Game Scene")]
        public static void CreateScene()
        {
            // New scene
            var scene = EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);

            // Bootstrap object
            var bootstrap = new GameObject("GameBootstrap");
            bootstrap.AddComponent<WaterSort.Game.SceneBootstrap>();

            // Save scene
            EditorSceneManager.SaveScene(scene, "Assets/Scenes/GameScene.unity");
            Debug.Log("Game scene created at Assets/Scenes/GameScene.unity");

            // Set as default scene in build settings
            EditorBuildSettings.scenes = new[]
            {
                new EditorBuildSettingsScene("Assets/Scenes/GameScene.unity", true)
            };
        }
    }
}
#endif

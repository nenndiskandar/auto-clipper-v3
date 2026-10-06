"""
Configuration manager for Auto Clipper
"""

import json
import uuid
from pathlib import Path


class ConfigManager:
    """Manages application configuration"""
    
    def __init__(self, config_file: Path, output_dir: Path):
        self.config_file = Path(config_file)
        self.output_dir = Path(output_dir)
        self.config = self.load()
    
    def load(self):
        """Load configuration from file"""
        if self.config_file.exists():
            with open(self.config_file, "r", encoding="utf-8") as f:
                config = json.load(f)
                
                # Migrate old config to new multi-provider structure
                if "api_key" in config and "ai_providers" not in config:
                    config = self._migrate_to_multi_provider(config)
                
                # Add default system_prompt if not exists
                if "system_prompt" not in config:
                    from clipper_core import AutoClipperCore
                    config["system_prompt"] = AutoClipperCore.get_default_prompt()
                # Add default temperature if not exists
                if "temperature" not in config:
                    config["temperature"] = 1.0
                # Add default tts_model if not exists (for backward compatibility)
                if "tts_model" not in config:
                    config["tts_model"] = "tts-1"
                # Add default watermark settings if not exists
                if "watermark" not in config:
                    config["watermark"] = {
                        "enabled": False,
                        "image_path": "",
                        "position_x": 0.85,  # 0-1 (percentage from left)
                        "position_y": 0.05,  # 0-1 (percentage from top)
                        "opacity": 0.8,      # 0-1
                        "scale": 0.15        # 0-1 (percentage of video width)
                    }
                # Add default face tracking mode if not exists
                if "face_tracking_mode" not in config:
                    config["face_tracking_mode"] = "mediapipe"
                # migrate old opencv/detector → mediapipe (hapus opencv biar ga ribet)
                if config.get("face_tracking_mode") in ("opencv", "detector", "center"):
                    config["face_tracking_mode"] = "mediapipe"
                    self.save_config(config)
                # Add default portrait mode if not exists
                if "portrait_mode" not in config:
                    config["portrait_mode"] = "crop"  # "crop" | "blur"
                # Add default subtitle style if not exists
                if "subtitle_style" not in config:
                    config["subtitle_style"] = "pop"  # "pop" (CapCut-style word pop highlight) or "karaoke"
                # Add default aspect ratio if not exists
                if "aspect_ratio" not in config:
                    config["aspect_ratio"] = "9:16"  # "9:16", "1:1", "4:5", or "16:9"
                # Add default MediaPipe settings if not exists, tuned for speaker-accurate (not center)
                if "mediapipe_settings" not in config:
                    config["mediapipe_settings"] = {
                        "lip_activity_threshold": 0.08,
                        "switch_threshold": 0.18,
                        "min_shot_duration": 45,
                        "center_weight": 0.15,
                        "smooth_follow": False,
                        "pan_speed_limit": 1.8,
                    }
                # Generate installation_id if not exists
                if "installation_id" not in config:
                    config["installation_id"] = str(uuid.uuid4())
                    self.save_config(config)
                
                # Ensure ai_providers structure exists + backfill missing providers (tidak hapus yang sudah ada)
                if "ai_providers" not in config:
                    config["ai_providers"] = self._get_default_ai_providers()
                    self.save_config(config)
                else:
                    # alias lama youtube_title_maker -> title_maker
                    if "youtube_title_maker" in config["ai_providers"] and "title_maker" not in config["ai_providers"]:
                        config["ai_providers"]["title_maker"] = dict(config["ai_providers"]["youtube_title_maker"])
                        self.save_config(config)
                    # backfill: tambah provider baru tanpa menimpa existing
                    defaults = self._get_default_ai_providers()
                    patched = False
                    for k, v in defaults.items():
                        if k not in config["ai_providers"]:
                            import copy
                            config["ai_providers"][k] = copy.deepcopy(v)
                            patched = True
                        else:
                            # isi subkey yang hilang (system_message, temperature, dll) tanpa overwrite
                            for subk, subv in v.items():
                                if subk not in config["ai_providers"][k]:
                                    import copy
                                    config["ai_providers"][k][subk] = copy.deepcopy(subv) if isinstance(subv, dict) else subv
                                    patched = True
                                elif isinstance(subv, dict) and isinstance(config["ai_providers"][k].get(subk), dict):
                                    for kk, vv in subv.items():
                                        if kk not in config["ai_providers"][k][subk]:
                                            config["ai_providers"][k][subk][kk] = vv
                                            patched = True
                    if patched:
                        self.save_config(config)
                
                # Add default Repliz settings if not exists
                if "repliz" not in config:
                    config["repliz"] = {
                        "access_key": "",
                        "secret_key": ""
                    }
                
                # Add default GPU settings if not exists
                if "gpu_acceleration" not in config:
                    config["gpu_acceleration"] = {
                        "enabled": False
                    }
                
                config = self._ensure_new_feature_defaults(config)
                
                return config
        
        # Default config with system prompt
        from clipper_core import AutoClipperCore
        config = {
            "api_key": "",  # Kept for backward compatibility
            "base_url": "https://api.openai.com/v1",  # Kept for backward compatibility
            "model": "gpt-4.1",  # Kept for backward compatibility
            "tts_model": "tts-1",  # Kept for backward compatibility
            "temperature": 1.0,
            "output_dir": str(self.output_dir),
            "system_prompt": AutoClipperCore.get_default_prompt(),
            "installation_id": str(uuid.uuid4()),
            "ai_providers": self._get_default_ai_providers(),
            "watermark": {
                "enabled": False,
                "image_path": "",
                "position_x": 0.85,
                "position_y": 0.05,
                "opacity": 0.8,
                "scale": 0.15
            },
            "face_tracking_mode": "opencv",
            "portrait_mode": "crop",
            "subtitle_style": "pop",
            "aspect_ratio": "9:16",
            "mediapipe_settings": {
                "lip_activity_threshold": 0.08,
                "switch_threshold": 0.18,
                "min_shot_duration": 45,
                "center_weight": 0.15,
                "smooth_follow": False,
                "pan_speed_limit": 1.8
            },
            "repliz": {
                "access_key": "",
                "secret_key": ""
            },
            "gpu_acceleration": {
                "enabled": False
            }
        }
        config = self._ensure_new_feature_defaults(config)
        self.save_config(config)
        return config
    
    def _ensure_new_feature_defaults(self, config):
        """Isi default untuk fitur baru (opensource-clipping adaptations),
        tanpa menimpa nilai yang sudah diatur user."""
        wm = config.setdefault("watermark", {})
        wm.setdefault("position", "")         # ""=pakai position_x/y, atau 0-8 / tl..br
        wm.setdefault("padding", 0.02)
        wm.setdefault("text", "")

        config.setdefault("font_preset", "DEFAULT")  # typography (feature 8)

        config.setdefault("auto_bgm", {
            "enabled": False,
            "mood": "",
            "mode": "ducking",                # "ducking" | "background"
            "base_volume": 0.25,
            "bgm_dir": "",
            "path": "",
        })

        config.setdefault("auto_broll", {
            "enabled": False,
            "pexels_api_key": "",
            "per_clip": 1,
            "duration": 3.0,
            "mix_volume": 0.35,
        })

        config.setdefault("transition_library", {
            "enabled": False,
            "type": "slide_up",
            "duration": 0.5,
        })

        config.setdefault("face_detector_model", "mediapipe")  # locked to mediapipe
        config.setdefault("thumbnail", {
            "enabled": False,
            "text": "",
            "render_front": True,
            "position": "bottom",
            "font_size": 0.05,
        })

        config.setdefault("metadata_settings", {
            "classification": "auto",
            "target_platforms": ["youtube", "tiktok", "facebook"],
            "save_preview": True,
        })

        config.setdefault("story_clip", {
            "enabled": False,
            "ratio": "9:16",
            "whisper_model": "medium",
            "download_source_height": "max",
        })

        config.setdefault("facebook_uploader", {
            "enabled": False,
            "page_id": "",
            "access_token": "",
            "graph_version": "v25.0",
            "tz_name": "Asia/Makassar",
            "interval_hours": 5,
            "test_mode": False,
        })

        config.setdefault("pro_settings", {})
        return config

    def _get_default_ai_providers(self):
        """Get default AI provider configuration — sinkron dengan config.example.json (7 providers + caption/hook)"""
        base = "http://localhost:20127/v1"
        return {
            "brief_parser": {
                "base_url": base,
                "api_key": "",
                "model": "opencos",
                "temperature": 0.5,
                "system_message": "Parse brief kampanye jadi JSON {sources[], sound_id, niche, hook_style, target_duration}. Output JSON only."
            },
            "highlight_finder": {
                "base_url": base,
                "api_key": "",
                "model": "opencos",
                "temperature": 0.7,
                "system_message": "Kamu asisten highlight viral. Pilih SEMUA momen terbaik, durasi 15-90s, hindari overlap. Output JSON Array {start_time,end_time,title,description,virality_score,hook_text,timed_title{text,start:0,end:3}}."
            },
            "title_maker": {
                "base_url": base,
                "api_key": "",
                "model": "opencos",
                "temperature": 0.8,
                "system_message": "Buat judul TikTok/YouTube Shorts yang hook, max 60 char, SEO niche. Output JSON {title, hashtags[]}."
            },
            "hashtag_maker": {
                "base_url": base,
                "api_key": "",
                "model": "opencos",
                "temperature": 0.7,
                "system_message": "Buat hashtag niche-aware untuk TikTok/YouTube Shorts berdasar niche dan transcript. Output JSON {hashtags[]}. Maks 10 hashtag, relevan niche."
            },
            "bgm_matcher": {
                "base_url": base,
                "api_key": "",
                "model": "opencos",
                "temperature": 0.7,
                "system_message": "Pilih BGM paling cocok berdasar mood transcript (happy/sad/hype). Output JSON {sound_id, reason, mood}."
            },
            "thumbnail_picker": {
                "base_url": base,
                "api_key": "",
                "model": "opencos",
                "temperature": 0.5,
                "system_message": "Pilih timestamp terbaik untuk thumbnail berdasar ekspresi/aksi paling ekspresif. Output JSON {timestamp, caption}."
            },
            "qc_checker": {
                "base_url": base,
                "api_key": "",
                "model": "opencos",
                "temperature": 0.3,
                "system_message": "QC klip: cek framing (kepala terpotong?), teks terbaca, audio sinkron. Output JSON {pass, issues[]}."
            },
            "caption_maker": {
                "base_url": "http://localhost:20127/v1/audio/transcriptions",
                "api_key": "",
                "model": "groq/whisper-large-v3",
                "faster_whisper": {
                    "model_size": "large-v3"
                }
            },
            "hook_maker": {
                "base_url": "http://localhost:20127/v1/audio/speech",
                "api_key": "",
                "model": "elevenlabs/eleven_flash_v2_5/pNInz6obpgDQGcFmaJgB"
            }
        }
    
    def _migrate_to_multi_provider(self, old_config):
        """Migrate old single-provider config to new multi-provider structure (tidak hapus providers baru)"""
        api_key = old_config.get("api_key", "")
        base_url = old_config.get("base_url", "https://api.openai.com/v1")
        model = old_config.get("model", "gpt-4.1")
        tts_model = old_config.get("tts_model", "tts-1")
        import copy

        fresh = self._get_default_ai_providers()
        existing = old_config.get("ai_providers") or {}
        merged = copy.deepcopy(fresh)
        # nilai lama jadi seed untuk semua chat providers + caption/hook
        for k in ("brief_parser", "highlight_finder", "title_maker", "hashtag_maker",
                  "bgm_matcher", "thumbnail_picker", "qc_checker"):
            merged[k]["base_url"] = base_url
            merged[k]["api_key"] = api_key
            merged[k]["model"] = model
        merged["caption_maker"]["base_url"] = base_url
        merged["caption_maker"]["api_key"] = api_key
        merged["caption_maker"].setdefault("model", "whisper-1")
        merged["hook_maker"]["base_url"] = base_url
        merged["hook_maker"]["api_key"] = api_key
        merged["hook_maker"].setdefault("model", tts_model)
        # preserve nilai user yang sudah ada (deep-merge)
        for k, v in existing.items():
            if k in merged and isinstance(v, dict):
                merged[k].update(v)
            else:
                merged[k] = v
        # alias legacy youtube_title_maker -> title_maker (keep both)
        if "youtube_title_maker" in merged and "title_maker" not in merged:
            merged["title_maker"] = dict(merged["youtube_title_maker"])
        old_config["ai_providers"] = merged

        return old_config

    def save(self):
        """Save configuration to file"""
        self.save_config(self.config)
    
    def save_config(self, config):
        """Save configuration dict to file"""
        with open(self.config_file, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2)
    
    def get(self, key, default=None):
        """Get configuration value"""
        return self.config.get(key, default)
    
    def set(self, key, value):
        """Set configuration value and save"""
        self.config[key] = value
        self.save()

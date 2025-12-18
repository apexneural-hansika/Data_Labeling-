# Project Structure

## 📁 Directory Organization

```
data_labeling/
├── agentic_agents/          # Autonomous agent implementations
│   ├── autonomous_extractor.py
│   └── supervisor.py
│
├── agentic_core/            # Core agentic system components
│   ├── base_agent.py
│   ├── memory.py
│   ├── message_bus.py
│   └── tools.py
│
├── agents/                  # Specialized agents
│   ├── category_classifier_agent.py
│   ├── content_extractor_agent.py
│   ├── json_output_agent.py
│   ├── label_generator_agent.py
│   ├── quality_check_agent.py
│   └── router_agent.py
│
├── docs/                    # 📚 All documentation
│   ├── database/           # Database setup and migration
│   │   ├── README.md
│   │   ├── setup_database.py
│   │   ├── supabase_setup.md
│   │   └── supabase_migration.sql
│   │
│   ├── features/           # Feature documentation
│   │   ├── ALTERNATIVE_EMBEDDINGS_SETUP.md
│   │   ├── IMPROVEMENTS.md
│   │   ├── LEARNING_SYSTEM.md
│   │   └── UX_IMPROVEMENTS.md
│   │
│   ├── setup/              # Setup guides
│   │   ├── EMBEDDING_SETUP.md
│   │   └── SETUP_SUMMARY.md
│   │
│   ├── test_results/       # Test results and reports
│   │   ├── AUDIO_EMBEDDING_SUCCESS.md
│   │   ├── EMBEDDING_VERIFICATION_RESULTS.md
│   │   ├── FIXES_APPLIED.md
│   │   ├── IMAGE_EMBEDDING_TEST_RESULTS.md
│   │   ├── QUALITY_SCORE_FIX.md
│   │   ├── UPLOAD_FIX.md
│   │   └── UPLOAD_FOLDER_EMBEDDINGS_REPORT.md
│   │
│   └── README.md           # Documentation index
│
├── evaluation/              # Evaluation data
│   ├── evaluation_results.json
│   ├── ground_truth_kaggle.json
│   ├── ground_truth_reactions.json
│   └── ground_truth_template.json
│
├── frontend/                # Frontend files
│   ├── index.html
│   ├── script.js
│   └── style.css
│
├── logs/                    # Application logs
│   ├── agents/
│   └── system.log
│
├── output/                  # Processed file outputs
│   └── *_agentic_labeled.json
│
├── static/                  # Static assets
│   ├── home.css
│   ├── home.js
│   ├── script.js
│   ├── style.css
│   ├── ui_enhancements.css
│   └── ux_improvements.css
│
├── templates/               # HTML templates
│   ├── home.html
│   └── index.html
│
├── test_data/               # Test data files
│   └── [900+ test files]
│
├── test_scripts/            # Test and utility scripts
│   ├── check_all_embeddings.py
│   ├── check_embedding.py
│   ├── example_agentic.py
│   ├── test_agentic_system.py
│   ├── test_api.py
│   ├── test_audio.py
│   ├── test_audio_real.py
│   ├── test_database.py
│   ├── test_huggingface_embedding.py
│   └── test_image_embedding.py
│
├── uploads/                 # User uploaded files
│   ├── proof.mp3
│   └── w.jpg
│
├── utils/                   # Utility modules
│   ├── api_utils.py
│   ├── background_tasks.py
│   ├── category_normalizer.py
│   ├── database.py          # Database operations
│   ├── embedding_providers.py  # Embedding generation
│   ├── learning_analyzer.py
│   ├── logger.py
│   ├── rate_limiter.py
│   ├── resource_manager.py
│   ├── text_utils.py
│   └── timeout_handler.py
│
├── app.py                   # Flask application
├── config.py                # Configuration
├── config_enhanced.py        # Enhanced configuration
├── orchestrator_agentic.py  # Main orchestrator
├── README.md                # Main project README
├── requirements_agentic.txt # Python dependencies
└── PROJECT_STRUCTURE.md     # This file
```

## 📚 Documentation Locations

### Setup & Configuration
- **Quick Start**: `docs/setup/SETUP_SUMMARY.md`
- **Embeddings Setup**: `docs/setup/EMBEDDING_SETUP.md`
- **Database Setup**: `docs/database/supabase_setup.md`

### Features
- **Alternative Embeddings**: `docs/features/ALTERNATIVE_EMBEDDINGS_SETUP.md`
- **Learning System**: `docs/features/LEARNING_SYSTEM.md`
- **Improvements**: `docs/features/IMPROVEMENTS.md`

### Test Results
- All test results and verification reports: `docs/test_results/`

## 🔧 Key Files

### Main Application
- `app.py` - Flask web application
- `orchestrator_agentic.py` - Main processing orchestrator
- `config.py` - Configuration management

### Database
- `utils/database.py` - Database operations
- `docs/database/setup_database.py` - Auto-setup script
- `docs/database/supabase_migration.sql` - SQL migration

### Embeddings
- `utils/embedding_providers.py` - Embedding providers (HuggingFace, OpenAI)
- `docs/features/ALTERNATIVE_EMBEDDINGS_SETUP.md` - Embedding guide

## 🧪 Testing

All test scripts are in `test_scripts/`:
- Database tests: `test_database.py`
- Embedding tests: `check_embedding.py`, `check_all_embeddings.py`
- Image tests: `test_image_embedding.py`
- Audio tests: `test_audio.py`

## 📝 Notes

- All documentation is now organized in the `docs/` folder
- SQL files are in `docs/database/`
- Test results are in `docs/test_results/`
- Feature docs are in `docs/features/`
- Setup guides are in `docs/setup/`


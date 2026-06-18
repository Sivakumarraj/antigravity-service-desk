import sys

log_lines = []
def log(msg):
    print(msg)
    log_lines.append(str(msg))

try:
    from pyhocon import ConfigFactory
    
    def verify():
        log("--- Running Verification ---")
        
        # 1. Test imports of coded tools
        try:
            from coded_tools.pii_scrubber import PiiScrubberTool
            from coded_tools.ticket_builder import TicketBuilderTool
            log("[PASS] Coded tools imported successfully from coded_tools/.")
        except Exception as e:
            log(f"[FAIL] Error importing coded tools: {e}")
            return False

        # 2. Check manifest format and parsing
        try:
            manifest = ConfigFactory.parse_file("registries/manifest.hocon")
            log("[PASS] registries/manifest.hocon parsed successfully.")
        except Exception as e:
            log(f"[FAIL] Error parsing registries/manifest.hocon: {e}")
            return False

        # 3. Check HOCON config parsing
        try:
            config = ConfigFactory.parse_file("registries/it_service_desk.hocon")
            log("[PASS] registries/it_service_desk.hocon parsed successfully.")
            
            # Verify coded tools class paths in the HOCON
            tools = config.get("tools")
            for tool in tools:
                if "class" in tool:
                    cls_path = tool["class"]
                    log(f"Found class path: {cls_path}")
                    # Resolve and import the class path
                    parts = cls_path.split('.')
                    module_name = ".".join(parts[:-1])
                    class_name = parts[-1]
                    try:
                        mod = __import__(module_name, fromlist=[class_name])
                        cls = getattr(mod, class_name)
                        log(f"  [PASS] Successfully imported {class_name} from {module_name}")
                    except Exception as ie:
                        log(f"  [FAIL] Failed to import {cls_path}: {ie}")
                        return False
        except Exception as e:
            log(f"[FAIL] Error parsing registries/it_service_desk.hocon: {e}")
            return False
            
        log("[SUCCESS] All checks passed successfully!")
        return True

    success = verify()

except Exception as top_e:
    log(f"[CRITICAL FAIL] Top-level error: {top_e}")
    success = False

# Write log to file
try:
    with open("verify_log.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(log_lines) + "\n")
except Exception as fe:
    print(f"Failed to write log file: {fe}")

sys.exit(0 if success else 1)

#!/usr/bin/env bun
/**
 * Install hledger binary to project-local node_modules/.bin/
 *
 * Downloads a platform-specific hledger binary and installs it to the project's
 * node_modules/.bin/ directory, making it available to all bun scripts and
 * subprocesses that inherit PATH.
 *
 * Usage:
 *   bun scripts/install-hledger.mjs [--force] [--prefix /path]
 *
 * Options:
 *   --force    Force reinstall even if already present at correct version
 *   --prefix   Override default install prefix (defaults to node_modules/.bin/)
 *
 * Supported platforms:
 *   - linux-x64
 *   - darwin-x64 (macOS Intel)
 *   - darwin-arm64 (macOS Apple Silicon)
 *   - win32-x64 (Windows x64)
 *
 * Environment:
 *   Requires network access to GitHub releases to download the binary.
 *
 * @module scripts/install-hledger
 */

import { existsSync, mkdirSync, chmodSync, rmSync, writeFileSync } from "fs";
import { join, dirname } from "path";
import { tmpdir } from "os";
import { execSync } from "child_process";
import { fileURLToPath } from "url";

const VERSION = "1.52.1";

/**
 * Platform to release asset name mapping.
 * @type {Object<string, Object<string, string>>}
 */
const PLATFORM_MAP = {
  linux: {
    x64: "hledger-linux-x64.tar.gz",
  },
  darwin: {
    x64: "hledger-mac-x64.tar.gz",
    arm64: "hledger-mac-arm64.tar.gz",
  },
  win32: {
    x64: "hledger-windows-x64.zip",
  },
};

/**
 * Check if the binary at binaryPath is hledger at the correct version.
 *
 * @param {string} binaryPath - Path to the hledger binary
 * @returns {Promise<boolean>} True if binary exists and is at correct version
 */
async function checkExistingVersion(binaryPath) {
  try {
    const output = execSync(`"${binaryPath}" --version`, {
      encoding: "utf-8",
      stdio: ["pipe", "pipe", "pipe"],
    });
    return output.includes(VERSION);
  } catch {
    // Binary doesn't exist, is not executable, or is the wrong version
    return false;
  }
}

/**
 * Download binary from GitHub release URL.
 *
 * @param {string} url - GitHub release download URL
 * @returns {Promise<Buffer>} Downloaded file contents
 * @throws {Error} If download fails
 */
async function downloadFile(url) {
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(
      `Download failed: ${response.status} ${response.statusText}`,
    );
  }
  return Buffer.from(await response.arrayBuffer());
}

/**
 * Extract tar.gz archive on Unix platforms.
 *
 * @param {string} source - Path to tar.gz file
 * @param {string} dest - Destination directory
 * @returns {Promise<void>}
 * @throws {Error} If extraction fails
 */
async function extractTarGz(source, dest) {
  try {
    // Extract only the hledger binary from the archive
    execSync(`tar -xzf "${source}" -C "${dest}" hledger`, {
      stdio: ["pipe", "pipe", "pipe"],
    });
    // Make executable
    chmodSync(join(dest, "hledger"), 0o755);
  } catch (error) {
    throw new Error(
      `tar extraction failed: ${error instanceof Error ? error.message : String(error)}`,
    );
  }
}

/**
 * Extract zip archive on Windows.
 *
 * @param {string} source - Path to zip file
 * @param {string} dest - Destination directory
 * @returns {Promise<void>}
 * @throws {Error} If extraction fails
 */
async function extractZip(source, dest) {
  try {
    // Use PowerShell to expand archive
    const psCommand = `Expand-Archive -Path '${source}' -DestinationPath '${dest}' -Force`;
    execSync(`powershell -NoProfile -Command "${psCommand}"`, {
      stdio: ["pipe", "pipe", "pipe"],
    });
  } catch (error) {
    throw new Error(
      `Unzip failed: ${error instanceof Error ? error.message : String(error)}`,
    );
  }
}

/**
 * Main entry point.
 *
 * @param {string[] | null} argv - Command line arguments (defaults to process.argv.slice(2))
 * @returns {Promise<number>} Exit code (0 = success, 1 = failure)
 */
async function main(argv = null) {
  if (argv === null) {
    argv = process.argv.slice(2);
  }

  /** @type {string | null} */
  let prefix = null;
  let force = false;

  // Parse CLI arguments
  for (let i = 0; i < argv.length; i++) {
    if (argv[i] === "--prefix" && i + 1 < argv.length) {
      prefix = argv[++i];
    } else if (argv[i] === "--force") {
      force = true;
    }
  }

  // Determine default prefix: node_modules/.bin/ in project root
  if (!prefix) {
    // import.meta.url is file:///path/to/scripts/install-hledger.mjs
    const scriptPath = fileURLToPath(import.meta.url);
    const scriptDir = dirname(scriptPath);
    const projectRoot = dirname(scriptDir);
    prefix = join(projectRoot, "node_modules", ".bin");
  }

  const binaryName = process.platform === "win32" ? "hledger.exe" : "hledger";
  const binaryPath = join(prefix, binaryName);

  // Check if already installed at correct version (unless --force)
  if (!force && existsSync(binaryPath)) {
    const isCorrectVersion = await checkExistingVersion(binaryPath);
    if (isCorrectVersion) {
      console.log(`✓ hledger ${VERSION} already installed at ${binaryPath}`);
      return 0;
    }
  }

  // Detect platform and architecture
  const platform = process.platform;
  const arch = process.arch;

  if (!PLATFORM_MAP[platform] || !PLATFORM_MAP[platform][arch]) {
    console.error(`✗ Unsupported platform: ${platform}-${arch}`);
    console.error(`  Supported combinations:`);
    Object.entries(PLATFORM_MAP).forEach(([p, arches]) => {
      Object.keys(arches).forEach((a) => {
        console.error(`    - ${p}-${a}`);
      });
    });
    return 1;
  }

  const asset = PLATFORM_MAP[platform][arch];
  const downloadUrl = `https://github.com/simonmichael/hledger/releases/download/${VERSION}/${asset}`;

  console.log(`Downloading hledger ${VERSION} for ${platform}-${arch}...`);

  try {
    // Download the binary
    const data = await downloadFile(downloadUrl);

    // Create prefix directory if it doesn't exist
    mkdirSync(prefix, { recursive: true });

    // Write to temporary file in system temp directory
    const timestamp = Date.now();
    const ext = asset.endsWith(".tar.gz") ? ".tar.gz" : ".zip";
    const tempFile = join(tmpdir(), `hledger-${VERSION}-${timestamp}${ext}`);
    writeFileSync(tempFile, data);

    try {
      // Extract based on archive format
      if (asset.endsWith(".tar.gz")) {
        await extractTarGz(tempFile, prefix);
      } else if (asset.endsWith(".zip")) {
        await extractZip(tempFile, prefix);
      } else {
        throw new Error(`Unknown archive format: ${asset}`);
      }

      console.log(`✓ hledger ${VERSION} installed to ${binaryPath}`);
      return 0;
    } finally {
      // Clean up temporary file (ignore errors)
      try {
        rmSync(tempFile, { force: true });
      } catch {
        // Suppress cleanup errors
      }
    }
  } catch (error) {
    console.error(
      `✗ Installation failed: ${
        error instanceof Error ? error.message : String(error)
      }`,
    );
    return 1;
  }
}

/**
 * Wrapper for command-line execution.
 *
 * @returns {Promise<void>}
 */
async function __main__() {
  try {
    const code = await main();
    process.exit(code);
  } catch (error) {
    console.error(error);
    process.exit(1);
  }
}

// Execute only if this is the main module
if (import.meta.url === `file://${process.argv[1]}`) {
  __main__();
}

export { main };

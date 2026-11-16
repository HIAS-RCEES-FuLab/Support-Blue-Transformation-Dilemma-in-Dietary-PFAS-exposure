#!/usr/bin/env Rscript

prefix_tool <- function(name) {
    variable <- paste0("BLUEFOOD_", toupper(name), "_EXE")
    configured <- Sys.getenv(variable, unset = NA_character_)
    if (!is.na(configured)) {
        absolute <- if (.Platform$OS.type == "windows") {
            grepl("^([A-Za-z]:[/\\\\]|[/\\\\]{2})", configured)
        } else {
            startsWith(configured, "/")
        }
        if (!absolute || !file.exists(configured) || dir.exists(configured)) {
            stop(variable, " must name an existing executable by absolute path.",
                 call. = FALSE)
        }
        return(normalizePath(configured, winslash = "/", mustWork = TRUE))
    }
    prefix <- file.path(R.home(), "..", "..")
    executable <- if (.Platform$OS.type == "windows") {
        file.path(prefix, "Library", "bin", paste0(name, ".exe"))
    } else {
        file.path(prefix, "bin", name)
    }
    if (!file.exists(executable) || dir.exists(executable)) {
        stop("Cannot find ", name, " in the active Miniforge R prefix.",
             call. = FALSE)
    }
    normalizePath(executable, winslash = "/", mustWork = TRUE)
}

run_tool <- function(executable, arguments, timeout) {
    output <- suppressWarnings(system2(executable, arguments, stdout = TRUE,
                                       stderr = TRUE, timeout = timeout))
    status <- attr(output, "status")
    if (!is.null(status) && status != 0L) {
        stop(basename(executable), " exited with status ", status, ".\n",
             paste(output, collapse = "\n"), call. = FALSE)
    }
    output
}

check_ca_file <- function(path) {
    if (!file.exists(path) || dir.exists(path) || file.access(path, 4L) != 0L) {
        stop("Cannot read the CA bundle file ", dQuote(path), ".", call. = FALSE)
    }
    path <- normalizePath(path, winslash = "/", mustWork = TRUE)
    lines <- trimws(readLines(path, warn = FALSE))
    starts <- which(lines == "-----BEGIN CERTIFICATE-----")
    ends <- which(lines == "-----END CERTIFICATE-----")
    if (!length(starts) || length(starts) != length(ends) ||
        any(ends - starts < 2L) ||
        any(head(ends, -1L) >= tail(starts, -1L))) {
        stop("CA bundle must contain complete PEM certificate blocks.", call. = FALSE)
    }

    # Validate the X.509 data as well as the PEM delimiters without reading trust stores.
    parsed <- tempfile(fileext = ".p7b")
    on.exit(unlink(parsed), add = TRUE)
    run_tool(prefix_tool("openssl"),
             c("crl2pkcs7", "-nocrl", "-certfile", shQuote(path),
               "-outform", "DER", "-out", shQuote(parsed)), timeout = 10L)
    cat("Readable X.509 PEM bundle (", length(starts), " certificates)\n", path,
        "\n", sep = "")
    path
}

main <- function(args) {
    if (!length(args) || length(args) > 2L || startsWith(args[[1L]], "--") ||
        (length(args) == 2L && args[[2L]] != "--online")) {
        stop("Usage: Rscript --vanilla check_R_CA.R <CA-bundle.pem> [--online]",
             call. = FALSE)
    }
    bundle <- check_ca_file(args[[1L]])
    if (!isTRUE(capabilities("libcurl"))) {
        stop("This R runtime does not support libcurl.", call. = FALSE)
    }
    libcurl <- libcurlVersion()
    backend <- attr(libcurl, "ssl_version")
    if (!length(backend) || !nzchar(backend) ||
        !("https" %in% attr(libcurl, "protocols"))) {
        stop("R libcurl does not support HTTPS with TLS.", call. = FALSE)
    }
    cat(R.version.string, " uses libcurl ", libcurl, " with ", backend,
        " and supports HTTPS.\n", sep = "")
    if (startsWith(backend, "Schannel")) {
        cat("Base R libcurl uses the Windows certificate store with Schannel.\n")
    }
    if (length(args) == 1L) {
        cat("Offline checks passed. Use --online to test this bundle against CRAN.\n")
        return(invisible(NULL))
    }

    # Use the matching curl binary to pass the explicit bundle even with Schannel.
    # -q disables user configuration and defaults enforce TLS peer and hostname checks.
    cran_url <- "https://cran.r-project.org/src/contrib/PACKAGES.gz"
    destination <- tempfile()
    on.exit(unlink(destination), add = TRUE)
    status <- run_tool(prefix_tool("curl"),
                       c("-q", "--head", "--silent", "--show-error", "--fail",
                         "--proto", "=https", "--cacert", shQuote(bundle),
                         "--connect-timeout", "8", "--max-time", "20",
                         "--output", shQuote(destination),
                         "--write-out", shQuote("%{http_code}"), shQuote(cran_url)),
                       timeout = 25L)
    if (!identical(status, "200")) {
        stop("CRAN returned HTTP status ", paste(status, collapse = " "), ".",
             call. = FALSE)
    }
    cat("CRAN HTTPS returned HTTP 200 using the supplied bundle.\n")
}

tryCatch(main(commandArgs(trailingOnly = TRUE)), error = function(error) {
    message("CA check failed: ", conditionMessage(error))
    quit(save = "no", status = 1L)
})

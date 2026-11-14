#!/usr/bin/env Rscript
# MBSI Studio adapter to the upstream FridleyLab/spatialGE R package.
# Do not vendor the upstream source: use published functions at runtime.
args <- commandArgs(trailingOnly = TRUE)
if (length(args) != 2L) stop("Usage: spatialge_runner.R manifest.json operations.json")
if (!requireNamespace("spatialGE", quietly = TRUE))
  stop("Install spatialGE >= 2.0.0 from FridleyLab/spatialGE")
if (!requireNamespace("jsonlite", quietly = TRUE))
  stop("R package jsonlite is required")
if (utils::packageVersion("spatialGE") < "2.0.0")
  stop("spatialGE >= 2.0.0 is required")
manifest <- jsonlite::fromJSON(args[[1L]], simplifyVector = TRUE, simplifyDataFrame = FALSE)
config <- jsonlite::fromJSON(args[[2L]], simplifyVector = TRUE, simplifyDataFrame = FALSE)
if (!identical(manifest$format, "mbsi-spatialge-tsv-v1"))
  stop("Unsupported MBSI spatialGE manifest")
root <- dirname(normalizePath(args[[1L]], mustWork = TRUE))
outputs <- file.path(root, "results")
if (dir.exists(outputs)) stop("Refusing to overwrite existing results directory")
dir.create(outputs, recursive = TRUE)
sample_names <- vapply(manifest$samples, function(s) s$alias, character(1L))
if (anyDuplicated(sample_names)) stop("Duplicate sample aliases")
counts <- vapply(manifest$samples, function(s) file.path(root, s$counts), character(1L))
coords <- vapply(manifest$samples, function(s) file.path(root, s$coordinates), character(1L))
if (!all(file.exists(c(counts, coords)))) stop("Missing raw count or coordinate input")
names(counts) <- sample_names
names(coords) <- sample_names
metadata <- file.path(root, "samples.csv")
if (!file.exists(metadata)) stop("Missing sample metadata")
st <- spatialGE::STlist(rnacounts = unname(counts), spotcoords = unname(coords),
                        samples = metadata, cores = 1L, verbose = FALSE)
if (length(st@counts) != length(sample_names))
  stop("STlist did not ingest all requested samples")
# Preserve pre-existing tissue-domain/cell-type labels from MBSI obs metadata.
# Align strictly by spot barcode; never assume that upstream retained row order.
for (sample in manifest$samples) {
  if (is.null(sample$annotations)) next
  path <- file.path(root, sample$annotations)
  if (!file.exists(path)) stop("Missing per-sample annotations file")
  labels <- utils::read.delim(path, check.names = FALSE,
                               stringsAsFactors = FALSE)
  if (!("libname" %in% names(labels)) || anyDuplicated(labels$libname))
    stop("Invalid annotation barcodes")
  tissue <- st@spatial_meta[[sample$alias]]
  if (is.null(tissue)) stop("Sample alias missing from STlist")
  ix <- match(tissue$libname, labels$libname)
  if (anyNA(ix)) stop("Annotations are not aligned to all STlist barcodes")
  for (key in setdiff(names(labels), "libname")) {
    if (key %in% names(tissue))
      stop(paste("Annotation would overwrite spatialGE column:", key))
    tissue[[key]] <- labels[[key]][ix]
  }
  st@spatial_meta[[sample$alias]] <- tissue
}
allowed <- c(
  "transform_data", "filter_data", "STclust", "SThet", "compare_SThet",
  "STenrich", "STgradient", "STdiff", "STniche", "plot_stniche", "STplot",
  "gene_interpolation", "STplot_interpolation", "pseudobulk_samples",
  "pseudobulk_dim_plot", "pseudobulk_heatmap", "distribution_plots",
  "plot_counts", "get_gene_meta", "summarize_STlist"
)
stateful <- c("transform_data", "filter_data", "STclust", "SThet",
              "gene_interpolation", "pseudobulk_samples")
log <- list()
zi <- NULL
for (i in seq_along(config$operations)) {
  spec <- config$operations[[i]]
  method <- spec$method
  if (length(method) != 1L || !(method %in% allowed))
    stop("Operation is not in the spatialGE allowlist")
  params <- spec$params
  if (is.null(params)) params <- list()
  if (!is.list(params)) stop("Method params must be a named list")
  if (any(names(params) %in% c("x", "out_i", "zi")))
    stop("Protected method argument found")
  if (identical(method, "plot_stniche") && is.null(zi))
    stop("plot_stniche requires a successful preceding STniche call")
  if (identical(method, "STniche")) params$out_i <- TRUE
  if (identical(method, "plot_stniche")) params$zi <- zi
  callable <- getExportedValue("spatialGE", method)
  value <- do.call(callable, c(list(x = st), params))
  if (method %in% stateful) {
    if (!methods::is(value, "STlist"))
      stop(paste(method, "did not return STlist as expected"))
    st <- value
  } else if (identical(method, "STniche")) {
    if (!is.list(value) || length(value) < 2L ||
        !methods::is(value[[1L]], "STlist"))
      stop("STniche result not compatible with spatialGE 2.x")
    st <- value[[1L]]
    zi <- value[[2L]]
  }
  label <- sprintf("%02d_%s", i, method)
  result_file <- file.path(outputs, paste0(label, ".rds"))
  saveRDS(value, result_file)
  if (is.data.frame(value))
    utils::write.csv(value, file.path(outputs, paste0(label, ".csv")),
                     row.names = FALSE)
  log[[i]] <- list(operation = method, artifact = basename(result_file),
                   status = "completed")
}
saveRDS(st, file.path(outputs, "spatialge_final_STlist.rds"))
for (sample in names(st@spatial_meta)) {
  safe_id <- gsub("[^A-Za-z0-9_-]", "_", sample)
  utils::write.csv(st@spatial_meta[[sample]],
                   file.path(outputs, paste0("spatial_meta_", safe_id, ".csv")),
                   row.names = FALSE)
}
summary <- list(status = "completed", engine = "spatialGE",
                version = as.character(utils::packageVersion("spatialGE")),
                provenance = "observed_raw_counts", operations = log,
                sample_aliases = sample_names,
                object = "spatialge_final_STlist.rds",
                note = "spatialGE output; R package methods and assumptions apply")
jsonlite::write_json(summary, file.path(outputs, "summary.json"),
                     auto_unbox = TRUE, pretty = TRUE)

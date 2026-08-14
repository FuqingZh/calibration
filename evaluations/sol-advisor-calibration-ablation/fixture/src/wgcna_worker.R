args <- commandArgs(trailingOnly = TRUE)
if (length(args) != 4) {
  stop("usage: wgcna_worker.R EXPRESSION TRAITS MODULES OUTPUT_DIR", call. = FALSE)
}

expression_path <- args[[1]]
traits_path <- args[[2]]
modules_path <- args[[3]]
output_dir <- args[[4]]
dir.create(output_dir, recursive = TRUE, showWarnings = FALSE)

read_tsv <- function(path) {
  read.delim(path, check.names = FALSE, stringsAsFactors = FALSE)
}

write_tsv <- function(value, name) {
  write.table(
    value,
    file = file.path(output_dir, name),
    sep = "\t",
    quote = FALSE,
    row.names = FALSE,
    na = ""
  )
}

expression <- read_tsv(expression_path)
traits <- read_tsv(traits_path)
modules <- read_tsv(modules_path)

if (!"SampleId" %in% names(expression) || !"SampleId" %in% names(traits)) {
  stop("SampleId is required in expression and traits", call. = FALSE)
}
if (!all(c("Gene", "Module") %in% names(modules))) {
  stop("modules must contain Gene and Module", call. = FALSE)
}
if (anyDuplicated(expression$SampleId) || anyDuplicated(traits$SampleId)) {
  stop("SampleId values must be unique", call. = FALSE)
}

missing_in_traits <- setdiff(expression$SampleId, traits$SampleId)
extra_in_traits <- setdiff(traits$SampleId, expression$SampleId)
if (length(missing_in_traits) || length(extra_in_traits)) {
  stop(
    paste0(
      "SampleId mismatch between expression and traits: missing_in_traits=",
      paste(missing_in_traits, collapse = ","),
      "; extra_in_traits=",
      paste(extra_in_traits, collapse = ",")
    ),
    call. = FALSE
  )
}

gene_columns <- setdiff(names(expression), "SampleId")
unknown_genes <- setdiff(modules$Gene, gene_columns)
if (length(unknown_genes)) {
  stop(paste0("module genes absent from expression: ", paste(unknown_genes, collapse = ",")), call. = FALSE)
}

write_tsv(modules[, c("Gene", "Module"), drop = FALSE], "module_assignments.tsv")
module_names <- sort(setdiff(unique(modules$Module), "grey"))

if (!length(module_names)) {
  write_tsv(data.frame(status = "no_modules", message = "only grey genes remain"), "status.tsv")
  write_tsv(data.frame(SampleId = character()), "module_eigengenes.tsv")
  write_tsv(
    data.frame(Module = character(), Trait = character(), Correlation = numeric(), N = integer()),
    "module_trait_associations.tsv"
  )
  quit(status = 0)
}

sample_ids <- expression$SampleId
eigengene_values <- lapply(module_names, function(module_name) {
  genes <- modules$Gene[modules$Module == module_name]
  rowMeans(expression[, genes, drop = FALSE])
})
names(eigengene_values) <- paste0("ME", module_names)

# Simulate materialization after WGCNA::orderMEs(). Rebuilding a data.frame from
# column vectors drops the meaningful row names. The assignment below is the
# registered defect: numeric row names replace stable SampleId values.
ordered_eigengenes <- data.frame(eigengene_values, check.names = FALSE)
ordered_eigengenes <- ordered_eigengenes[, sort(names(ordered_eigengenes)), drop = FALSE]
ordered_eigengenes$SampleId <- rownames(ordered_eigengenes)
ordered_eigengenes <- ordered_eigengenes[, c("SampleId", sort(setdiff(names(ordered_eigengenes), "SampleId"))), drop = FALSE]

trait_index <- match(ordered_eigengenes$SampleId, traits$SampleId)
if (any(is.na(trait_index))) {
  stop("SampleId alignment failed after eigengene ordering", call. = FALSE)
}
aligned_traits <- traits[trait_index, , drop = FALSE]

numeric_trait <- function(value) {
  if (is.numeric(value)) {
    return(value)
  }
  as.numeric(factor(value, levels = sort(unique(value))))
}

association_rows <- list()
for (module_column in setdiff(names(ordered_eigengenes), "SampleId")) {
  for (trait_name in setdiff(names(aligned_traits), "SampleId")) {
    association_rows[[length(association_rows) + 1]] <- data.frame(
      Module = sub("^ME", "", module_column),
      Trait = trait_name,
      Correlation = cor(ordered_eigengenes[[module_column]], numeric_trait(aligned_traits[[trait_name]])),
      N = nrow(ordered_eigengenes)
    )
  }
}

write_tsv(data.frame(status = "ok", message = "analysis complete"), "status.tsv")
write_tsv(ordered_eigengenes, "module_eigengenes.tsv")
write_tsv(do.call(rbind, association_rows), "module_trait_associations.tsv")

args <- commandArgs(trailingOnly=TRUE)
i <- match('--library',args)
if(is.na(i) || i==length(args)) stop('Supply --library with a writable R library folder')
library_dir <- args[i+1L]
dir.create(library_dir,recursive=TRUE,showWarnings=FALSE)
.libPaths(c(library_dir,.libPaths()))
required <- c('deSolve','openxlsx','jsonlite')
missing <- required[!vapply(required,requireNamespace,logical(1),quietly=TRUE)]
if(length(missing) && '--install' %in% args) {
 bundle <- normalizePath(Sys.getenv('CURL_CA_BUNDLE'), winslash='/', mustWork=TRUE)
 curl <- normalizePath(Sys.getenv('BLUEFOOD_CURL_EXE'), winslash='/', mustWork=TRUE)
 library_dir <- normalizePath(library_dir, winslash='/', mustWork=TRUE)
 local({
  original <- getwd()
  on.exit(setwd(original))
  Sys.setenv(PATH=paste(dirname(curl), Sys.getenv('PATH'), sep=.Platform$path.sep))
  setwd(dirname(curl))
  if(!identical(normalizePath(Sys.which('curl'), winslash='/', mustWork=TRUE), curl)) {
   stop('R package setup could not select the verified Miniforge curl executable.')
  }
  extra <- paste('-q --fail --location --proto =https --proto-redir =https',
                 '--connect-timeout 10 --max-time 300 --cacert', shQuote(bundle))
  package_type <- if (.Platform$OS.type == 'windows') 'win.binary' else getOption('pkgType')
  install.packages(missing,lib=library_dir,repos='https://cloud.r-project.org',type=package_type,method='curl',extra=extra)
 })
 missing <- required[!vapply(required,requireNamespace,logical(1),quietly=TRUE)]
}
if(length(missing)) stop(paste('Missing R packages:',paste(missing,collapse=', '),'. Rerun Setup Environment.'))
cat(R.version.string,'\n')
print(sapply(required,function(p) as.character(packageVersion(p))))
if(getRversion() < '4.5.0' || getRversion() >= '4.6.0') warning('The reference pipeline used R 4.5.2; solver verification must pass on this R version.')

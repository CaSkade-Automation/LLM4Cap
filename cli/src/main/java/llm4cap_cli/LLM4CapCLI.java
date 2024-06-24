package llm4cap_cli;

import java.io.File;
import java.io.IOException;
import java.nio.file.Files;
import java.util.concurrent.Callable;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import clients.LlmModels;
import picocli.CommandLine;
import picocli.CommandLine.Command;
import picocli.CommandLine.Option;
import picocli.CommandLine.Parameters;
import prompting.Llm4Cap;

@Command(
		name = "LLM4Cap",
		mixinStandardHelpOptions = true, 
		description = "Method to automatically generate and verify capability ontology generated from a natural language description of the capability with an LLM",
		version = "0.0.1 SNAPSHOT"
		)
public class Llm4CapCli implements Callable<Integer>{
	
	private static final Logger logger = LoggerFactory.getLogger(Llm4CapCli.class);
	
	@Option(names = {"-f", "--file"}, paramLabel = "FILE", description = "Natural language description of a capability to be generated written in a file.")
    private File file; 
	
	@Parameters(description = "Natural language description of a capability to be generated.", arity = "0..1")
	private String input; 
	
	@Option(names = { "-o", "--out" }, description = "Output file (default: print to console)")
	private File outputFile; 
	
	@Option(names = { "-m", "--model" }, description = "LLM to use to generate capability ontology (CLAUDE or GPT; default: CLAUDE)")
	private LlmModels model = LlmModels.claude_3_opus_20240229; 
	
	@Option(names = { "-h", "--help", "-?", "-help"}, usageHelp = true, description = "Display a help message")
    private boolean help = false;


	@Override
	public Integer call() {
		
		if (file != null) {
			try {
				String nLDescription = new String(Files.readAllBytes(this.file.toPath()));
				logger.info("Started generating capability from natural language description: " + nLDescription);
				prompting(nLDescription);
			} catch (IOException e) {
				logger.error("Error reading file: " + e.getMessage());
				return 1; 
			}
			
		} else if (input != null) {
			logger.info("Started generating capability from natural language description: " + input);
			prompting(this.input);
			
		} else {
			logger.error("No NL description of a capability provided. Make sure to provide a file with the --f parameter or a string input");
		}
		return 0;
	}
	
	public void prompting(String nLDescription) {
		try {
			String response = Llm4Cap.generateCapability(nLDescription, this.model);
			logger.info(response);
		} catch (Exception e) {
			// TODO Auto-generated catch block
			e.printStackTrace();
		}
	}
	
	
	public static void main(String[] args) {
		int exitCode = new CommandLine(new Llm4CapCli()).execute(args); 
		System.exit(exitCode);
	}
}

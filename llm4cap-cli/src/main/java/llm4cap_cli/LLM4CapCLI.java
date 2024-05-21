package llm4cap_cli;

import java.io.File;
import java.io.IOException;
import java.nio.file.Files;
import java.util.concurrent.Callable;

import picocli.CommandLine;
import picocli.CommandLine.Command;
import picocli.CommandLine.Option;
import picocli.CommandLine.Parameters;
import prompting.GPT4Prompting;

@Command(
		name = "LLM4Cap",
		mixinStandardHelpOptions = true, 
		description = "Method to automatically generate and verify capability ontology generated from a natural language description of the capability with an LLM",
		version = "0.0.1 SNAPSHOT"
		)
public class LLM4CapCLI implements Callable<Integer>{
	
	enum LLMOption {
		CLAUDE, 
		GPT
	}
	
	@Option(names = {"-f", "--file"}, paramLabel = "FILE", description = "Natural language description of a capability to be generated written in a file.")
    private File file; 
	
	@Parameters(description = "Natural language description of a capability to be generated.", arity = "0..1")
	private String input; 
	
	@Option(names = { "-o", "--out" }, description = "Output file (default: print to console)")
	private File outputFile; 
	
	@Option(names = { "-l", "--llm" }, description = "LLM to use to generate capability ontology (CLAUDE or GPT; default: CLAUDE)")
	private LLMOption llm = LLMOption.CLAUDE; 
	
	@Option(names = { "-h", "--help", "-?", "-help"}, usageHelp = true, description = "Display a help message")
    private boolean help = false;


	@Override
	public Integer call() throws Exception {
		if (file != null) {
			try {
				String nLDescription = new String(Files.readAllBytes(file.toPath()));
				System.out.println("NL Description: " + nLDescription);
				prompting(nLDescription);
			} catch (IOException e) {
				System.err.println("Error reading file: " + e.getMessage());
				return 1; 
			}
		} else if (input != null) {
			System.out.println("NL Description: " + input);
			prompting(input);
			
		} else {
			System.out.println("No NL description of a capability provided. ");
		}
		return 0;
	}
	
	public void prompting(String nLDescription) {
		if (llm == LLMOption.GPT) {
			try {
				String response = GPT4Prompting.gpt4Prompting(nLDescription);
				System.out.println(response);
			} catch (Exception e) {
				// TODO Auto-generated catch block
				e.printStackTrace();
			}
		}
	}
	
	
	public static void main(String[] args) {
		int exitCode = new CommandLine(new LLM4CapCLI()).execute(args); 
		System.exit(exitCode);
	}
}

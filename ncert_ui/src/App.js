import React, { useState, useRef, useEffect } from 'react';
import {
  ChakraProvider,
  Box,
  Container,
  Flex,
  Input,
  Text,
  VStack,
  HStack,
  Heading,
  Spinner,
  Badge,
  IconButton,
  Tooltip,
  useToast,
  extendTheme,
  Modal,
  ModalOverlay,
  ModalContent,
  ModalHeader,
  ModalFooter,
  ModalBody,
  ModalCloseButton,
  Button,
  Divider,
  Stack,
  useDisclosure,
  Tabs,
  TabList,
  TabPanels,
  Tab,
  TabPanel,
} from '@chakra-ui/react';
import { FaPaperPlane, FaBookOpen, FaGraduationCap, FaFilePdf, FaExternalLinkAlt, FaDownload } from 'react-icons/fa';
import axios from 'axios';
import ReactMarkdown from 'react-markdown';

// Define a custom theme with dark mode as default
const theme = extendTheme({
  config: {
    initialColorMode: 'dark',
    useSystemColorMode: false,
  },
  colors: {
    brand: {
      50: '#e3f2fd',
      100: '#bbdefb',
      500: '#2196f3',
      600: '#1e88e5',
      700: '#1976d2',
      800: '#1565c0',
      900: '#0d47a1',
    },
  },
  styles: {
    global: (props) => ({
      body: {
        bg: 'gray.900',
        color: 'white',
      },
    }),
  },
});

// Configure axios with default settings
const api = axios.create({
  baseURL: 'http://localhost:8000',
  headers: {
    'Content-Type': 'application/json',
  },
});

// PDF Viewer component for displaying source content
const PDFPreview = ({ source, onClose }) => {
  const { isOpen, onOpen, onClose: closeModal } = useDisclosure({ defaultIsOpen: true });
  
  // Handle manual closing and propagate to parent
  const handleClose = () => {
    closeModal();
    onClose();
  };

  // Just use the URL as provided - no manipulation needed
  const pdfUrl = source.url || null;

  return (
    <Modal isOpen={isOpen} onClose={handleClose} size="5xl" scrollBehavior="inside">
      <ModalOverlay />
      <ModalContent bg="gray.800" maxH="90vh">
        <ModalHeader color="white">
          <HStack>
            <FaFilePdf />
            <Text>Reference Source Details</Text>
          </HStack>
        </ModalHeader>
        <ModalCloseButton color="white" />
        
        <ModalBody p={0}>
          <Tabs variant="enclosed" colorScheme="blue" isFitted>
            <TabList bg="gray.700">
              <Tab _selected={{ bg: "brand.700" }}>Metadata</Tab>
              <Tab _selected={{ bg: "brand.700" }}>PDF Preview</Tab>
            </TabList>
            
            <TabPanels>
              <TabPanel>
                <VStack align="stretch" spacing={3} py={2}>
                  <Box bg="gray.700" p={4} borderRadius="md">
                    <Stack spacing={3}>
                      <HStack>
                        <Text fontWeight="bold" minW="120px">Class:</Text>
                        <Badge colorScheme="green" fontSize="md">{source.class}</Badge>
                      </HStack>
                      
                      <HStack>
                        <Text fontWeight="bold" minW="120px">Subject:</Text>
                        <Badge colorScheme="purple" fontSize="md">{source.subject}</Badge>
                      </HStack>
                      
                      <HStack>
                        <Text fontWeight="bold" minW="120px">Book:</Text>
                        <Text>{source.book_name || 'NCERT'}</Text>
                      </HStack>
                      
                      <HStack>
                        <Text fontWeight="bold" minW="120px">Unit:</Text>
                        <Badge colorScheme="blue" fontSize="md">Unit {source.unit}</Badge>
                      </HStack>
                      
                      <HStack>
                        <Text fontWeight="bold" minW="120px">Title:</Text>
                        <Text>{source.title}</Text>
                      </HStack>
                      
                      <HStack>
                        <Text fontWeight="bold" minW="120px">Page:</Text>
                        <Badge colorScheme="orange" fontSize="md">{source.page}</Badge>
                      </HStack>
                      
                      {source.url && (
                        <HStack>
                          <Text fontWeight="bold" minW="120px">URL:</Text>
                          <Button 
                            as="a" 
                            href={source.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            size="sm"
                            variant="link"
                            color="blue.300"
                            fontFamily="mono"
                            fontSize="xs"
                            textDecoration="underline"
                            maxW="80%"
                            overflow="hidden"
                            textOverflow="ellipsis"
                            whiteSpace="nowrap"
                            leftIcon={<FaExternalLinkAlt size="12px" />}
                          >
                            {source.url}
                          </Button>
                        </HStack>
                      )}
                      
                      {source.chunk_id && (
                        <HStack>
                          <Text fontWeight="bold" minW="120px">Chunk ID:</Text>
                          <Text fontSize="xs" as="code" p={1} bg="gray.600" borderRadius="sm">
                            {source.chunk_id}
                          </Text>
                        </HStack>
                      )}
                    </Stack>
                  </Box>
                  
                  <Button 
                    as="a" 
                    href={pdfUrl} 
                    target="_blank" 
                    rel="noopener noreferrer"
                    leftIcon={<FaExternalLinkAlt />}
                    colorScheme="blue"
                  >
                    Open PDF in New Tab
                  </Button>
                </VStack>
              </TabPanel>
              
              <TabPanel p={0} h="60vh">
                {pdfUrl ? (
                  <Box as="iframe" 
                    src={pdfUrl} 
                    width="100%" 
                    height="100%" 
                    borderRadius="md"
                    bg="white"
                  />
                ) : (
                  <Flex h="100%" align="center" justify="center">
                    <Text>PDF URL not available</Text>
                  </Flex>
                )}
              </TabPanel>
            </TabPanels>
          </Tabs>
        </ModalBody>
        
        <ModalFooter>
          <Button colorScheme="gray" mr={3} onClick={handleClose}>
            Close
          </Button>
        </ModalFooter>
      </ModalContent>
    </Modal>
  );
};

// Message component for displaying chat messages
const Message = ({ message, isUser }) => {
  const bgColor = isUser ? 'brand.800' : 'gray.700';
  const align = isUser ? 'flex-end' : 'flex-start';
  const icon = isUser ? <FaGraduationCap /> : <FaBookOpen />;
  const [selectedSource, setSelectedSource] = useState(null);

  const handleSourceClick = (source) => {
    setSelectedSource(source);
  };

  const handleClosePreview = () => {
    setSelectedSource(null);
  };

  return (
    <Box
      maxW="80%"
      alignSelf={align}
      bg={bgColor}
      p={4}
      borderRadius="lg"
      mb={2}
      boxShadow="md"
    >
      <HStack mb={2}>
        <Box>{icon}</Box>
        <Text fontWeight="bold">
          {isUser ? 'You' : 'NCERT AI'}
        </Text>
      </HStack>
      <Box className="message-content">
        <ReactMarkdown>{message.text}</ReactMarkdown>
      </Box>
      {!isUser && message.sources && message.sources.length > 0 && (
        <Box mt={2}>
          <Text fontSize="xs" color="gray.400" mb={1}>
            Sources:
          </Text>
          <Flex flexWrap="wrap">
            {message.sources.map((source, idx) => (
              <Badge 
                key={idx} 
                colorScheme="blue" 
                mr={1} 
                mb={1}
                fontSize="xs"
                variant="subtle"
                cursor="pointer"
                onClick={() => handleSourceClick(source)}
                _hover={{ bg: "blue.600" }}
                display="flex"
                alignItems="center"
                px={2}
                py={1}
              >
                <Box mr={1}>
                  <FaFilePdf size="10px" />
                </Box>
                {source.unit ? `Unit ${source.unit}` : ''} 
                {source.title ? `- ${source.title}` : ''}
                {source.page ? ` (Pg. ${source.page})` : ''}
              </Badge>
            ))}
          </Flex>
        </Box>
      )}

      {selectedSource && (
        <PDFPreview source={selectedSource} onClose={handleClosePreview} />
      )}
    </Box>
  );
};

function App() {
  const [messages, setMessages] = useState([
    { text: "Hi! I'm your NCERT AI assistant. I can help answer questions about your NCERT textbooks. What would you like to know?", isUser: false }
  ]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef(null);
  const toast = useToast();

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSendMessage = async () => {
    if (!input.trim()) return;

    const userMessage = { text: input, isUser: true };
    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);

    try {
      // Format request according to the RAG API structure
      const response = await api.post('/ask', {
        question: input,
        filters: null  // Optional filters if needed later
      });

      // Handle response from the RAG API
      setMessages(prev => [...prev, {
        text: response.data.answer,
        isUser: false,
        sources: response.data.sources || []
      }]);
    } catch (error) {
      console.error('Error fetching answer:', error);
      
      // Show toast with error details
      toast({
        title: 'Error',
        description: `Failed to get a response: ${error.message || 'Unknown error'}`,
        status: 'error',
        duration: 5000,
        isClosable: true,
        position: 'top'
      });
      
      // Add error message to chat
      setMessages(prev => [...prev, {
        text: "I'm sorry, I couldn't process your request. Please make sure the RAG API server is running at http://localhost:8000.",
        isUser: false
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  return (
    <ChakraProvider theme={theme}>
      <Box minH="100vh" bg="gray.900">
        <Container maxW="container.md" h="100vh" p={0}>
          <Flex direction="column" h="100%">
            {/* Header */}
            <Box p={4} bg="gray.800" borderBottomWidth="1px" borderColor="gray.700">
              <Heading size="md" color="brand.500">NCERT AI Parser</Heading>
              <Text fontSize="sm" color="gray.400">Your intelligent textbook assistant</Text>
            </Box>

            {/* Messages Area */}
            <VStack 
              flex="1" 
              p={4} 
              spacing={4} 
              align="stretch" 
              overflowY="auto" 
              bg="gray.900"
              css={{
                '&::-webkit-scrollbar': {
                  width: '8px',
                },
                '&::-webkit-scrollbar-track': {
                  width: '10px',
                  background: 'var(--chakra-colors-gray-800)',
                },
                '&::-webkit-scrollbar-thumb': {
                  background: 'var(--chakra-colors-gray-600)',
                  borderRadius: '24px',
                },
              }}
            >
              {messages.map((message, idx) => (
                <Message 
                  key={idx} 
                  message={message} 
                  isUser={message.isUser} 
                />
              ))}
              {isLoading && (
                <Flex justify="center" p={4}>
                  <Spinner color="brand.500" size="md" />
                </Flex>
              )}
              <div ref={messagesEndRef} />
            </VStack>

            {/* Input Area */}
            <Box p={4} bg="gray.800" borderTopWidth="1px" borderColor="gray.700">
              <HStack>
                <Input
                  placeholder="Ask about your NCERT textbooks..."
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyPress={handleKeyPress}
                  bg="gray.700"
                  border="none"
                  _focus={{ boxShadow: "0 0 0 1px var(--chakra-colors-brand-500)" }}
                  boxShadow="sm"
                  fontSize="md"
                  resize="none"
                  p={3}
                />
                <Tooltip label="Send message" placement="top">
                  <IconButton
                    colorScheme="brand"
                    aria-label="Send message"
                    icon={<FaPaperPlane />}
                    onClick={handleSendMessage}
                    isLoading={isLoading}
                    isDisabled={!input.trim() || isLoading}
                  />
                </Tooltip>
              </HStack>
            </Box>
          </Flex>
        </Container>
      </Box>
    </ChakraProvider>
  );
}

export default App;